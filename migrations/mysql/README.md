# MySQL 迁移目录

`001_initial_schema_cascade.py` 提供了 MySQL 8.x 完整的初始化建表 SQL：

- 使用 MySQL 原生 `ENUM(...)` 类型列，相比 `CHECK` 约束更高效，可被可视化工具识别
- 使用 `utf8mb4_unicode_ci` 支持 emoji 和多语言（中日韩俄等）
- 多对多表 `feedback_customer` 两外键均带 `ON DELETE CASCADE ON UPDATE CASCADE`，删除反馈或客户不留孤儿
- `feedbacks.updated_at` 用 `ON UPDATE CURRENT_TIMESTAMP(3)` 自动维护毫秒级时间戳
- `feedbacks.topic_id` 带 `ON DELETE SET NULL`，删除主题时反馈自动归类为"未分类"

## 两种执行方式

**方式 1：直接跑 SQL**
```bash
mysql -u root -p your_db < <(python3 001_initial_schema_cascade.py)
```

**方式 2：用 Alembic**
```bash
pip install pymysql alembic
alembic -c alembic.ini upgrade head
```

## 回滚

```bash
mysql -u root -p your_db < <(python3 001_initial_schema_cascade.py down)
```
