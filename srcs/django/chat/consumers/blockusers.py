import json
from django.contrib.auth import get_user_model
from chat.models import BlockedUser
from channels.db import database_sync_to_async, sync_to_async
from asgiref.sync import sync_to_async

User = get_user_model()


class BlockConsumer:

    async def block_or_unblock_user(self, data):
        """
        Block or unblock a user, depending on the current state.
        """
        user_id = data.get("user_id")
        user = await self.get_user_by_id(user_id)
        from_user = self.scope["user"]                                                          # Get the user who is blocking/unblocking, owner of the WebSocket connection
        is_currently_blocked = await self.is_blocked(from_user.id, user.id)                     # Check if the user is currently blocked

        if is_currently_blocked:                                                                # If the user is currently blocked, unblock them                            
            await self.unblock_user(from_user, user)
            type = "unblocked"                                                                  # type is the action that will be performed                 
        else:
            await self.block_user(from_user, user)
            type = "blocked"

        await self.send(text_data=json.dumps({"type": type, "username": user.username}))        # Send the action to the client
        await self.send_blocked_users()                                                         # Send the updated list of blocked users to the client

    async def is_blocked(self, blocker_id, blocked_id):
        """
        Check if a user is blocked.
        """
        return await database_sync_to_async(
            BlockedUser.objects.filter(
                blocker_id=blocker_id, blocked_id=blocked_id
            ).exists
        )()

    async def block_user(self, blocker, blocked):
        """
        Block a user.
        """
        await sync_to_async(BlockedUser.objects.create)(
            blocker=blocker, blocked=blocked
        )

    async def unblock_user(self, blocker, blocked):
        """
        Unblock a user.
        """
        await sync_to_async(BlockedUser.objects.filter(
            blocker=blocker,
            blocked=blocked
        ).delete)()             # Converting Django's synchronous delete operation to async and executing it with () at the end

    async def get_blocked_users(self, user):
        """
        Get the list of blocked users. Use list() to convert the queryset to a list of dictionaries.
        Each dictionary contains the username of the blocked user. Example: [{'username': 'user1'}, {'username': 'user2'}]
        """
        blocked = await sync_to_async(list)(user.blocking.select_related("blocked"))            # Use select_related to avoid additional queries
        return [{"username": b.blocked.username} for b in blocked]

    async def send_blocked_users(self):
        """
        Send the list of blocked users to the client.
        """
        blocked_users = await self.get_blocked_users(self.scope["user"])
        await self.send(
            text_data=json.dumps(
                {"type": "blocked_users", "blocked_users": blocked_users}
            )
        )

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        return User.objects.get(id=user_id)
