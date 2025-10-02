# 认证 Library 使用指南

## 概述

本 library 提供了一套完整的用户认证解决方案，将原本散落在 `views.py` 中的认证逻辑模块化，提高代码复用性和维护性。

## 模块结构

```
library/auth/
├── __init__.py                 # 模块导出
├── authentication_service.py   # 认证服务核心
├── user_profile_service.py    # 用户资料管理
├── validation_service.py      # 输入验证服务
├── response_formatter.py      # 响应格式化器
├── usage_examples.py          # 使用示例
└── README.md                  # 本文件
```

## 快速开始

### 1. 导入模块

```python
from library.auth import (
    AuthenticationService,
    UserProfileService,
    ValidationService, 
    AuthResponseFormatter
)
```

### 2. 基本使用

#### 用户认证

```python
# 认证用户
auth_result = AuthenticationService.authenticate_user(
    username="testuser",
    password="password123", 
    request=request
)

if auth_result['success']:
    user = auth_result['user']
    print(f"用户 {user.username} 认证成功")
else:
    print(f"认证失败: {auth_result['message']}")
```

#### 输入验证

```python
# 验证登录数据
is_valid, errors = ValidationService.validate_login_data({
    'username': 'testuser',
    'password': 'password123'
})

if not is_valid:
    print(f"验证失败: {errors}")
```

#### 响应格式化

```python
# 成功响应
return AuthResponseFormatter.login_success_response(
    user=user,
    message="登录成功"
)

# 错误响应
return AuthResponseFormatter.error_response(
    message="用户名或密码错误",
    error_code="INVALID_CREDENTIALS",
    status_code=401
)
```

## 核心组件详解

### 🔐 AuthenticationService

**主要功能：**
- 用户认证和登录
- 用户登出和 Session 管理
- 权限检查
- 密码更改

**常用方法：**

```python
# 认证用户
auth_result = AuthenticationService.authenticate_user(username, password, request)

# 用户登出
logout_result = AuthenticationService.logout_user(request, force_clear_all_sessions=True)

# 检查权限
permission_result = AuthenticationService.check_user_permissions(user, ['auth.add_user'])

# 更改密码
change_result = AuthenticationService.change_user_password(user, old_password, new_password)

# 获取 Session 信息
session_info = AuthenticationService.get_session_info(request)
```

### 👤 UserProfileService

**主要功能：**
- 获取和格式化用户资料
- 创建和更新用户 Profile
- 用户显示名称处理
- 用户数据验证

**常用方法：**

```python
# 获取用户完整资料
profile_result = UserProfileService.get_user_profile_data(user)
user_data = profile_result['user']

# 创建/更新用户资料
profile_result = UserProfileService.create_or_update_user_profile(
    user=user,
    profile_data={'bio': '新的个人简介'}
)

# 获取显示名称
display_name = UserProfileService.get_user_display_name(user)

# 获取安全信息（不含敏感数据）
safe_info = UserProfileService.get_user_safe_info(user)
```

### ✅ ValidationService

**主要功能：**
- 登录数据验证
- 注册数据验证
- 密码更改验证
- 邮箱和用户名格式验证
- 输入数据清理

**常用方法：**

```python
# 验证登录数据
is_valid, errors = ValidationService.validate_login_data(data)

# 验证注册数据  
is_valid, errors = ValidationService.validate_registration_data(data)

# 验证邮箱格式
is_valid = ValidationService.validate_email("test@example.com")

# 清理输入数据
clean_input = ValidationService.sanitize_input(user_input, max_length=100)

# 验证必填字段
is_valid, errors = ValidationService.validate_required_fields(
    data, ['username', 'email', 'password']
)
```

### 📋 AuthResponseFormatter

**主要功能：**
- 统一的成功响应格式
- 统一的错误响应格式
- 特定场景响应（登录、登出、验证错误等）
- 支持 DRF 和 Django 原生 JsonResponse

**常用方法：**

```python
# 成功响应
return AuthResponseFormatter.success_response(
    user=user, 
    message="操作成功",
    data={'extra': 'data'}
)

# 错误响应
return AuthResponseFormatter.error_response(
    message="操作失败",
    error_code="CUSTOM_ERROR", 
    status_code=400
)

# 登录成功响应
return AuthResponseFormatter.login_success_response(
    user=user,
    session_info=session_info
)

# 验证错误响应
return AuthResponseFormatter.validation_error_response(
    validation_errors={'username': '用户名不能为空'}
)

# 权限不足响应
return AuthResponseFormatter.forbidden_response("权限不足")
```

## 在 Django Views 中的使用

### Class-based View 示例

```python
@method_decorator(csrf_exempt, name='dispatch')
class UserLoginView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # 🆕 使用 ValidationService 验证
            is_valid, errors = ValidationService.validate_login_data(data)
            if not is_valid:
                return AuthResponseFormatter.validation_error_response(
                    errors, use_drf=False
                )
            
            # 🆕 使用 AuthenticationService 认证
            auth_result = AuthenticationService.authenticate_user(
                data['username'], data['password'], request
            )
            
            if auth_result['success']:
                # 🆕 使用 AuthResponseFormatter 格式化响应
                return AuthResponseFormatter.login_success_response(
                    user=auth_result['user'], use_drf=False
                )
            else:
                return AuthResponseFormatter.error_response(
                    auth_result['message'], 
                    error_code=auth_result['error_code'],
                    status_code=401,
                    use_drf=False
                )
                
        except Exception as e:
            return AuthResponseFormatter.server_error_response(
                str(e), use_drf=False
            )
```

### DRF Function-based View 示例

```python
@api_view(['POST'])
@permission_classes([AllowAny])
def user_login_api(request):
    # 验证输入
    is_valid, errors = ValidationService.validate_login_data(request.data)
    if not is_valid:
        return AuthResponseFormatter.validation_error_response(errors)
    
    # 认证用户
    auth_result = AuthenticationService.authenticate_user(
        request.data['username'], 
        request.data['password'], 
        request
    )
    
    if auth_result['success']:
        return AuthResponseFormatter.login_success_response(auth_result['user'])
    else:
        return AuthResponseFormatter.error_response(
            auth_result['message'],
            status_code=401
        )
```

## 重构效果对比

### 重构前（原始 UserLoginView）

```python
# 原始代码：约 60 行，逻辑混合
def post(self, request):
    try:
        data = json.loads(request.body)
        username = data.get('username', '')
        password = data.get('password', '')
        
        # 手动验证
        if not username or not password:
            return JsonResponse({
                'success': False,
                'message': '用户名和密码不能为空'
            }, status=400)
        
        # 手动认证
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                
                # 手动获取用户资料
                try:
                    profile = UserProfile.objects.get(user=user)
                    bio = profile.bio
                except UserProfile.DoesNotExist:
                    bio = ''
                
                # 手动格式化响应
                return JsonResponse({
                    'success': True,
                    'message': '登入成功',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        # ... 更多字段
                    }
                }, status=200)
            else:
                return JsonResponse({
                    'success': False,
                    'message': '该帐号已被停用'
                }, status=401)
        else:
            return JsonResponse({
                'success': False,
                'message': '用户名或密码错误'
            }, status=401)
    except Exception as e:
        # 手动错误处理...
```

### 重构后（使用 Library）

```python
# 重构后：约 25 行，逻辑清晰
def post(self, request):
    try:
        data = json.loads(request.body)
        
        # 🆕 统一验证
        is_valid, errors = ValidationService.validate_login_data(data)
        if not is_valid:
            return AuthResponseFormatter.validation_error_response(errors, use_drf=False)
        
        # 🆕 统一认证
        auth_result = AuthenticationService.authenticate_user(
            data['username'], data['password'], request
        )
        
        # 🆕 统一响应格式化
        if auth_result['success']:
            return AuthResponseFormatter.login_success_response(
                auth_result['user'], use_drf=False
            )
        else:
            return AuthResponseFormatter.error_response(
                auth_result['message'], 
                error_code=auth_result['error_code'],
                status_code=401, 
                use_drf=False
            )
            
    except Exception as e:
        return AuthResponseFormatter.server_error_response(str(e), use_drf=False)
```

## 优势总结

### ✨ 代码简化
- **减少 50% 代码量**：从 60 行减少到 25 行
- **提高可读性**：逻辑清晰，职责分离
- **减少重复**：认证逻辑复用，避免复制粘贴

### 🔧 维护性
- **集中管理**：认证逻辑集中在 Library 中
- **统一修改**：修改一处，所有调用处受益
- **容易扩展**：新增功能只需扩展 Library

### 🧪 测试友好
- **单元测试**：Library 组件独立，易于单元测试
- **模拟测试**：可以轻松模拟各种认证场景
- **集成测试**：统一的接口便于集成测试

### 🛡️ 安全性
- **统一验证**：所有输入都经过标准化验证
- **安全响应**：统一的错误处理，避免信息泄露
- **Session 管理**：统一的 Session 和权限管理

### 🚀 性能优化
- **减少重复计算**：公共逻辑复用
- **优化查询**：UserProfile 查询优化
- **缓存友好**：便于添加缓存层

## 最佳实践

### 1. 输入验证优先
```python
# ✅ 好的做法：总是先验证输入
is_valid, errors = ValidationService.validate_login_data(data)
if not is_valid:
    return AuthResponseFormatter.validation_error_response(errors)
```

### 2. 使用统一的响应格式
```python
# ✅ 好的做法：使用 AuthResponseFormatter
return AuthResponseFormatter.success_response(user=user)

# ❌ 避免：手动构造响应
return JsonResponse({'success': True, 'user': {...}})
```

### 3. 错误处理要全面
```python
# ✅ 好的做法：捕获具体异常
try:
    auth_result = AuthenticationService.authenticate_user(...)
    # 处理结果...
except Exception as e:
    logger.error(f"Authentication error: {str(e)}")
    return AuthResponseFormatter.server_error_response()
```

### 4. 日志记录要详细
```python
# ✅ 好的做法：记录关键操作
logger.info(f"User login attempt: {username}")
if auth_result['success']:
    logger.info(f"User login successful: {username}")
else:
    logger.warning(f"User login failed: {username} - {auth_result['message']}")
```

## 扩展指南

### 添加新的认证方法

```python
# 在 AuthenticationService 中添加
@staticmethod
def authenticate_with_token(token: str, request: HttpRequest = None) -> Dict:
    """使用 Token 认证"""
    # 实现 Token 认证逻辑
    pass
```

### 添加新的验证规则

```python
# 在 ValidationService 中添加
@staticmethod
def validate_strong_password(password: str) -> Tuple[bool, str]:
    """验证强密码策略"""
    # 实现强密码验证逻辑
    pass
```

### 添加新的响应类型

```python
# 在 AuthResponseFormatter 中添加
@staticmethod
def two_factor_required_response(user_id: int, use_drf: bool = True) -> Response:
    """需要二次验证的响应"""
    # 实现二次验证响应格式
    pass
```

## 总结

通过使用这套认证 Library，你可以：

1. **大幅简化代码**：减少重复代码，提高开发效率
2. **提升代码质量**：统一的验证、认证和响应处理
3. **增强安全性**：标准化的安全措施和错误处理
4. **便于维护**：集中管理认证逻辑，易于扩展和修改
5. **提高测试覆盖率**：模块化设计便于单元测试

建议在新项目中直接使用这套 Library，在现有项目中逐步重构使用。