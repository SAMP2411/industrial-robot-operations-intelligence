# Phase 1: working product shell

Implemented the incident-first FastAPI shell, full versioned domain model, PostgreSQL/SQLite persistence, Alembic baseline migration, generic connector contract, basic CRUD, existing YAML asset-registry adapter, and incident-only operator console. The `legacy/autonomy_demo/ros2_ws/src/` ROS workspace remains buildable and is referenced as the optional autonomy data generator.

Verification: schema creation, OpenAPI contract, YAML registry import, legacy test, ROS build, and ROS smoke test.
