from app.models.user import UserRepository
from app.models.db import init_db

init_db()
# 测试注册用户
UserRepository.create_user("admin", "123456")
print("注册用户成功")
print("根据条件查询", UserRepository.get_user_by_username("admin"))
print("验证用户", UserRepository.verify_user("admin", "123456"))
