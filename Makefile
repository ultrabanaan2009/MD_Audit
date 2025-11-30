# MD Audit Makefile

.PHONY: install dev serve build clean test

# 安装所有依赖
install:
	pip install -r requirements.txt
	cd frontend && npm install

# 开发模式：前端热更新 + 后端
dev:
	@echo "启动开发模式..."
	@echo "前端: http://localhost:5173"
	@echo "后端: http://localhost:8000"
	cd frontend && npm run dev & \
	python -m md_audit.main serve --reload

# 生产模式：一键构建并启动
serve:
	cd frontend && npm run build
	python -m md_audit.main serve

# 仅构建前端
build:
	cd frontend && npm run build

# 运行测试
test:
	pytest tests/ -v

# 清理
clean:
	rm -rf web/static/assets
	rm -f web/static/index.html
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
