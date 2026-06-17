# PostgreSQL 迁移目录

`001_initial_schema_cascade.py` 提供了 PostgreSQL 的完整初始化建表 SQL：

- 使用原生 `CREATE TYPE ... AS ENUM` 定义 `priority_level` 和 `feedback_status`（比 SAEnum 在 Postgres 上更优，能被 psql/dbeaver 等工具识别）
- 多对多表 `feedback_customer` 两外键均带 `ON DELETE CASCADE ON UPDATE CASCADE`，删除客户或反馈不留孤儿行
- `status_changes.feedback_id` 带 `ON DELETE CASCADE`
- `feedbacks.updated_at` 使用 `BEFORE UPDATE` 触发器自动维护（MySQL 8 可类似用 ON UPDATE 子句）
- `feedbacks.topic_id` 带 `ON DELETE SET NULL`，删除主题时反馈自动归类为"未分类"，而非被级联删除

## 两种执行方式

**方式 1：直接跑 SQL**
```bash
psql -d your_db -U your_user -h localhost \
     -c "$(python3 001_initial_schema_cascade.py)"
```

**方式 2：用 Alembic**
```bash
pip install psycopg2-binary alembic
alembic -c alembic.ini upgrade head
```

## 回滚

```bash
psql -d your_db -U your_user -c "$(python3 001_initial_schema_cascade.py down)"
```
