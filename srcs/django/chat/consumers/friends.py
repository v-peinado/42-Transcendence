import json
from django.contrib.auth import get_user_model
from chat.models import FriendRequest, Friendship
from channels.db import database_sync_to_async
from django.db.models import Q

User = get_user_model()


class FriendRequestsConsumer:
    async def send_friend_request(self, data):
        """
        Send a friend request to another user, and notify the user who received the request and the user who sent it.
        """
        to_user_id = data.get("to_user_id")
        from_user = await self.get_user_by_id(self.user_id)
        to_user = await self.get_user_by_id(to_user_id)

        already_friends = await self.check_friendship_exists(from_user, to_user)
        if already_friends:
            return await self.send_error("You are already friends.")

        friend_request, created = await self.create_friend_request(from_user, to_user)          #Boolean created is True if a new object was created, False if it already existed
        if not created:
            return await self.send_error("Friend request already exists")

        await self.notify_pending_requests(to_user_id)                                          #Notify the user who received the friend request
        await self.notify_pending_requests(from_user.id, sent=True)                             #send=True if the user sent the friend request

    async def accept_friend_request(self, data):
        """
        Accept a friend request and create a friendship between the two users,
        then notify both users of the updated friend list.
        """
        request_id = data.get("request_id")
        if not request_id:
            await self.send_error("Friend request ID not provided.")
            return

        friend_request = await self.get_friend_request(request_id)
        if friend_request.to_user_id != self.user_id:
            await self.send_error("No tienes permiso para aceptar esta solicitud.")
            return

        await self.create_friendship(                                                           #Create a friendship between the two users
            friend_request.from_user_id, friend_request.to_user_id
        )
        await self.delete_friend_request(friend_request)                                        #Delete the friend request

        from_user = await self.get_user_by_id(friend_request.from_user_id)
        to_user = await self.get_user_by_id(friend_request.to_user_id)

        await self.notify_pending_requests(from_user.id, sent=True)
        await self.notify_pending_requests(to_user.id)
        await self.send_friend_list(from_user.id)
        await self.send_friend_list(to_user.id)

    async def reject_friend_request(self, data):
        """
        Refuse a friend request and notify the user who sent it.
        """
        request_id = data.get("request_id")
        if not request_id:
            await self.send_error("Friend request ID not provided.")
            return

        friend_request = await self.get_friend_request(request_id)
        if (
            friend_request.to_user_id != self.user_id
            and friend_request.from_user_id != self.user_id
        ):
            await self.send_error("No tienes permiso para rechazar esta solicitud.")
            return

        await self.delete_friend_request(friend_request)

        from_user = await self.get_user_by_id(friend_request.from_user_id)
        to_user = await self.get_user_by_id(friend_request.to_user_id)

        await self.notify_pending_requests(from_user.id, sent=True)
        await self.notify_pending_requests(to_user.id)

    async def notify_pending_requests(self, user_id, sent=False):
        """
        Notify the user of their pending friend requests or sent friend requests.
        Use flag sent to determine the user's role in the request.
        This functions returns a list of pending requests or sent requests, depending on the value of the sent flag.
        """
        if sent:
            pending_data = await self.get_sent_requests_data(user_id)
        else:
            pending_data = await self.get_pending_requests_data(user_id)

        pending_list = []
        for req in pending_data:                                                               
            if sent:
                pending_list.append(
                    {
                        "request_id": req["id"],
                        "to_user_id": req["to_user_id"],
                        "to_user_username": req["to_user__username"],
                    }
                )
            else:
                pending_list.append(
                    {
                        "request_id": req["id"],
                        "from_user_id": req["from_user_id"],
                        "from_user_username": req["from_user__username"],
                    }
                )

        await self.channel_layer.group_send(                                                    #Send the pending list to the users in the group
            f"user_{user_id}",
            {"type": "pending_list", "pending": pending_list, "sent": sent},                    #sent=True if the user sent the friend request and False if the user received the request
        )

    async def pending_list(self, event):
        """
        Send the pending friend requests or sent friend requests to the user in the group.
        Type is pending_friend_requests if the user received the requests, and sent_friend_requests if the user sent the requests.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": (
                        "pending_friend_requests"
                        if not event["sent"]
                        else "sent_friend_requests"
                    ),
                    "pending": event["pending"],
                }
            )
        )

    async def send_friend_list(self, user_id):
        friends = await self.get_friends(user_id)
        await self.channel_layer.group_send(
            f"user_{user_id}", {"type": "friend_list_update", "friends": friends}
        )

    async def friend_list_update(self, event):
        await self.send(
            text_data=json.dumps(
                {"type": "friend_list_update", "friends": event["friends"]}
            )
        )

    async def send_error(self, message):
        await self.send(text_data=json.dumps({"type": "error", "message": message}))

    @database_sync_to_async
    def get_friend_request(self, request_id):
        return FriendRequest.objects.get(id=request_id)

    @database_sync_to_async
    def check_friendship_exists(self, from_user, to_user):
        return Friendship.objects.filter(
            Q(user1=from_user, user2=to_user) | Q(user1=to_user, user2=from_user)               # Q objects are used to make complex queries, such as OR queries
        ).exists()

    @database_sync_to_async
    def create_friend_request(self, from_user, to_user):
        return FriendRequest.objects.get_or_create(from_user=from_user, to_user=to_user)

    @database_sync_to_async
    def create_friendship(self, from_user_id, to_user_id):
        if from_user_id > to_user_id:
            from_user_id, to_user_id = to_user_id, from_user_id
        Friendship.objects.create(user1_id=from_user_id, user2_id=to_user_id)

    @database_sync_to_async
    def delete_friend_request(self, friend_request):
        friend_request.delete()

    @database_sync_to_async
    def get_friendship(self, friendship_id):
        return Friendship.objects.get(id=friendship_id)

    async def delete_friendship(self, friendship_id):
        friendship = await self.get_friendship(friendship_id)
        user1 = friendship.user1_id
        user2 = friendship.user2_id
        await self.delete_friendship_append(friendship_id)
        await self.send_friend_list(user1)
        await self.send_friend_list(user2)

    @database_sync_to_async
    def delete_friendship_append(self, friendship_id):
        friendship = Friendship.objects.get(id=friendship_id)
        friendship.delete()

    @database_sync_to_async
    def get_friends(self, user_id):
        return list(                                                                            # Convert the QuerySet to a list                                       
            Friendship.objects.filter(Q(user1_id=user_id) | Q(user2_id=user_id))
            .select_related("user1", "user2")
            .values("user1_id", "user1__username", "user2_id", "user2__username", "id")
        )

    @database_sync_to_async
    def get_pending_requests_data(self, user_id):
        return list(
            FriendRequest.objects.filter(to_user_id=user_id)
            .select_related("from_user")
            .values("id", "from_user_id", "from_user__username")
        )

    @database_sync_to_async
    def get_sent_requests_data(self, user_id):
        return list(
            FriendRequest.objects.filter(from_user_id=user_id)
            .select_related("to_user")
            .values("id", "to_user_id", "to_user__username")
        )
