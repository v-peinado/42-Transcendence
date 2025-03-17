from .base import ChatConsumer
import json
from django.contrib.auth import get_user_model
from chat.models import Group, GroupMembership
from channels.db import database_sync_to_async

User = get_user_model()


class GroupsConsumer:

    async def create_group(self, data):
        """
        Create a group and add the current user to it.
        Note: The group name must be unique, because the group name is formed by id.
        Notify the user about the new group.
        """
        group_name = data.get("group_name")
        group = await self.create_group_in_db(group_name, self.user_id)

        await self.add_user_to_group_in_db(group.id, self.user_id)
        await self.channel_layer.group_add(group.channel_name, self.channel_name)
        await self.send_user_groups()

    async def add_user_to_group(self, data):
        """
        Add user(s) to a group. Can add multiple users at once.
        """
        group_id = data.get("group_id")
        user_ids = data.get("user_ids", [])                                                     # If user_ids is not provided, it will be an empty list  
        single_user_id = data.get("user_id")

        for uid in user_ids:
            group = await self.add_user_to_group_in_db(group_id, uid)
            user_channel_name = ChatConsumer.connected_users.get(uid)
            if user_channel_name:
                await self.channel_layer.group_add(
                    f"chat_group_{group.id}", user_channel_name
                )

        if single_user_id:
            group = await self.add_user_to_group_in_db(group_id, single_user_id)
            user_channel_name = ChatConsumer.connected_users.get(single_user_id)
            if user_channel_name:
                await self.channel_layer.group_add(
                    f"chat_group_{group.id}", user_channel_name
                )

        await self.channel_layer.group_send(
            f"chat_group_{group.id}",
            {"type": "notify_group_update", "group_id": group.id},
        )

    async def leave_group(self, data):
        """
        Laeve a group. Notify the group about the user leaving.
        """
        group_id = data.get("id")
        group_name = data.get("groupname")
        user_id = data.get("userId")

        await self.remove_user_from_group_in_db(group_id, user_id)
        await self.channel_layer.group_discard(
            f"chat_group_{group_id}", self.channel_name
        )
        await self.channel_layer.group_send(
            f"chat_group_{group_id}",
            {"type": "notify_group_update", "group_id": group_id},
        )
        await self.send_user_groups()

    @database_sync_to_async
    def remove_user_from_group_in_db(self, group_id, user_id):
        GroupMembership.objects.filter(group_id=group_id, user_id=user_id).delete()
        if not GroupMembership.objects.filter(group_id=group_id).exists():                      # If there are no more members in the group, delete the group
            Group.objects.filter(id=group_id).delete()

    async def notify_group_update(self, event):
        group_id = event["group_id"]
        group_members = await self.get_group_members(group_id)
        for member in group_members:
            await self.send_user_groups(member["id"])

    async def send_user_groups(self, user_id=None):
        if user_id is None:
            user_id = self.user_id
        groups = await self.get_user_groups(user_id)
        await self.send(text_data=json.dumps({"type": "user_groups", "groups": groups}))

    async def user_groups(self, event):
        await self.send(
            text_data=json.dumps({"type": "user_groups", "groups": event["groups"]})
        )

    @database_sync_to_async
    def get_user_groups(self, user_id):
        memberships = GroupMembership.objects.filter(user_id=user_id).select_related(
            "group"
        )
        groups = []
        for membership in memberships:
            group = membership.group
            members = GroupMembership.objects.filter(group=group).select_related("user")
            group_members = [
                {"id": member.user.id, "username": member.user.username}
                for member in members
            ]
            groups.append(
                {"id": group.id, "name": group.name, "members": group_members}
            )
        return groups

    async def join_group_channels(self):
        groups = await self.get_user_groups(self.user_id)
        for group in groups:
            await self.channel_layer.group_add(
                f"chat_group_{group['id']}", self.channel_name
            )

    async def leave_group_channels(self):
        groups = await self.get_user_groups(self.user_id)
        for group in groups:
            await self.channel_layer.group_discard(
                f"chat_group_{group['id']}", self.channel_name
            )

    @database_sync_to_async
    def get_group_members(self, group_id):
        memberships = GroupMembership.objects.filter(group_id=group_id).select_related(
            "user"
        )
        return [
            {"id": membership.user.id, "username": membership.user.username}
            for membership in memberships
        ]

    @database_sync_to_async
    def create_group_in_db(self, group_name, creator_id):
        creator = User.objects.get(id=creator_id)
        group = Group.objects.create(name=group_name, creator=creator)
        GroupMembership.objects.create(group=group, user=creator)
        return group

    @database_sync_to_async
    def add_user_to_group_in_db(self, group_id, user_id):
        group = Group.objects.get(id=group_id)
        user = User.objects.get(id=user_id)
        if not GroupMembership.objects.filter(group=group, user=user).exists():
            GroupMembership.objects.create(group=group, user=user)
        return group
