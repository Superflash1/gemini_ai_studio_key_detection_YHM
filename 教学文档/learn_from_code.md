# Flask SQLite数据库自动创建机制

在Flask应用中使用SQLAlchemy时，数据库文件的创建是自动完成的。让我们通过代码来理解这个过程：

## 1. 数据库配置

首先在Flask应用中配置SQLite数据库：

```python
# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gemini_keys.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'
```

这里的配置告诉Flask：
- 使用SQLite数据库
- 数据库文件名为`gemini_keys.db`
- 数据库文件将存储在应用的`instance`目录中

## 2. 创建数据库目录

确保存放数据库的目录存在：

```python
# 确保数据库目录存在
os.makedirs('instance', exist_ok=True)
```

- `exist_ok=True`参数确保即使目录已存在也不会报错
- `instance`是Flask的约定目录，用于存储实例相关文件

## 3. 初始化数据库

通过调用初始化函数创建数据库：

```python
def create_tables():
    """创建数据库表并初始化默认设置"""
    with app.app_context():
        db.create_all()
```

## 4. 自动创建机制说明

1. **SQLAlchemy自动创建**
   - 当配置`SQLALCHEMY_DATABASE_URI`指向SQLite文件时
   - SQLAlchemy会自动在指定位置创建数据库文件

2. **`db.create_all()`作用**
   - 根据models.py中定义的模型类
   - 自动创建所有数据库表
   - 如果表已存在则跳过

3. **Flask的instance目录**
   - Flask应用默认使用instance目录存储实例文件
   - 数据库文件通常放在这个目录下
   - 这是Flask的最佳实践约定

4. **目录确保机制**
   - 使用`os.makedirs()`确保目录存在
   - `exist_ok=True`参数防止目录已存在时报错

## 5. 执行顺序

1. 应用启动时首先确保instance目录存在
2. 然后执行create_tables()函数
3. SQLAlchemy检查数据库文件是否存在，不存在则创建
4. 最后创建所有定义的数据库表

这种自动创建机制使得开发者不需要手动创建数据库文件，简化了应用的部署和初始化过程。
