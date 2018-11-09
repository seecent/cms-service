# Leads管理系统后台服务
Leads管理系统后台服务

1. 安装依赖文件 pip install -r requirements.txt

2. 开发运行项目 hug -f app.py

3. 使用alembic进行数据库版本管理
3.1 初始化alembic: alembic init migrations 使用之前，先在项目根目录进行初始化
3.2 自动创建版本：alembic revision --autogenerate -m "initdb"
3.3 更新数据库表到最新版本：alembic upgrade head
3.4 或者生成sql文件进行离线更新：alembic upgrade head --sql > migration.sql
3.5 SQL Server varchar可能导致乱码，SQL Server表采用nvarchar

4. 生成API帮助文档
4.1 在lms-service同级目录创建help_doc目录，打开命令行切换到help_doc目录，执行: sphinx-quickstart创建sphinx工程。
4.2 配置help_doc/source/conf.py文件
注意：conf.py需要添加autodoc_mock_imports=['hug', 'sqlalchemy', 'falcon', 'hashids', 'Crypto']，否则make html会报错
4.3 执行命令sphinx-apidoc -o ./source ../lms-service/
4.4 执行make html
4.5 进入help_doc/build/html查看生成的html帮助文档

5. 生产环境使用gunicorn部署，运行命令：gunicorn -c gunicorn.conf app:__hug_wsgi__ & 
# cms-service
