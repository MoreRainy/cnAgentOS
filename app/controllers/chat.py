import json
import tornado.web
import tornado.gen
import time

from app.controllers.base import BaseHandler
from app.models.conversation import ConversationRepository, MessageRepository
from app.models.user import UserRepository


class ChatHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user = UserRepository.get_user_by_username(self.current_user)
        conversations = ConversationRepository.get_conversations_by_user(user["id"])
        self.render(
            "chat.html",
            title="智能问数",
            username=self.current_user,
            conversations=conversations,
        )


class ChatApiHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self):
        user = UserRepository.get_user_by_username(self.current_user)
        conversations = ConversationRepository.get_conversations_by_user(user["id"])
        result = {
            "code": 0,
            "data": [
                {"id": c["id"], "title": c["title"], "updated_at": c["updated_at"]}
                for c in conversations
            ],
        }
        self.write(result)

    @tornado.web.authenticated
    async def post(self):
        user = UserRepository.get_user_by_username(self.current_user)
        body = json.loads(self.request.body)
        title = body.get("title", "新对话")
        cid = ConversationRepository.create_conversation(user["id"], title)
        self.write({"code": 0, "data": {"id": cid}})


class ChatSendHandler(BaseHandler):
    @tornado.web.authenticated
    async def post(self):
        user = UserRepository.get_user_by_username(self.current_user)
        body = json.loads(self.request.body)
        content = body.get("content", "").strip()
        if not content:
            self.set_status(400)
            self.write({"code": -1, "msg": "问题不能为空"})
            return

        cid = body.get("conversation_id")
        if not cid:
            cid = ConversationRepository.create_conversation(user["id"])
        else:
            cid = int(cid)

        MessageRepository.add_message(cid, "user", content)

        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Connection", "keep-alive")
        self.set_header("X-Accel-Buffering", "no")

        answer = "这是一个模拟回复。您问的是: " + content
        for i in range(0, len(answer), 3):
            chunk = answer[i : i + 3]
            data = json.dumps({"delta": chunk, "done": False}, ensure_ascii=False)
            self.write(f"data: {data}\n\n")
            await self.flush()
            await tornado.gen.sleep(0.05)

        MessageRepository.add_message(cid, "assistant", answer)

        done_data = json.dumps(
            {"delta": "", "done": True, "conversation_id": cid}, ensure_ascii=False
        )
        self.write(f"data: {done_data}\n\n")
        await self.flush()


class ChatDetailHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self, conversation_id):
        user = UserRepository.get_user_by_username(self.current_user)
        conversation = ConversationRepository.get_conversation(int(conversation_id))
        if not conversation or conversation["user_id"] != user["id"]:
            self.set_status(404)
            self.write({"code": -1, "msg": "对话不存在"})
            return

        messages = MessageRepository.get_messages_by_conversation(int(conversation_id))
        result = {
            "code": 0,
            "data": {
                "conversation": {
                    "id": conversation["id"],
                    "title": conversation["title"],
                },
                "messages": [
                    {
                        "role": m["role"],
                        "content": m["content"],
                        "created_at": m["created_at"],
                    }
                    for m in messages
                ],
            },
        }
        self.write(result)


class ChatDeleteHandler(BaseHandler):
    @tornado.web.authenticated
    async def post(self, conversation_id):
        user = UserRepository.get_user_by_username(self.current_user)
        ConversationRepository.delete_conversation(int(conversation_id), user["id"])
        self.write({"code": 0, "msg": "已删除"})
