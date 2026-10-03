# yiban-protocol

易班网页 OAuth + nightAttendance 链路的**洁净室解析库**：只做两件事——
**解析**（bytes/dict → 结构化数据）与**构造**（结构化参数 → 请求体/URL）。

不做：网络请求、会话/cookie 管理、重试、验证码求解、异步 API。全部同步纯函数，
无 I/O、无日志、无全局状态。核心仅依赖标准库。

## 安装

```bash
pip install yiban-protocol            # 纯解析/构造，零第三方依赖
pip install 'yiban-protocol[crypto]'  # 追加 RSA 加密（pycryptodome）
```

`[crypto]` extra 仅用于 `yiban_protocol.crypto`。不安装时核心模块完全可用；
`encrypt_password` 通过惰性属性暴露，未装依赖而导入 crypto 模块会抛出带安装指引的
`ImportError`。

## 用法示例

```python
# 以下全部为纯函数，不发起任何请求；网络/会话由调用方自行负责。
from yiban_protocol import (
    parse_authorize_page, parse_usersure_response, parse_identity,
    parse_sign_position, build_usersure_form, build_sign_in_body, encrypt_password,
)

# 1. 授权页 -> page_use（即 usersure 的 ajax_sign）+ 登录公钥
page = parse_authorize_page(html)
# 2. 用公钥加密密码（需 [crypto] extra）
pwd = encrypt_password("secret", page.public_key_pem)
# 3. 构造 usersure 请求体，然后由调用方 POST 到
#    https://oauth.yiban.cn/code/usersure?ajax_sign={page.page_use}
body = build_usersure_form("13800000000", pwd, client_id, redirect_uri)
# 4. 解析 usersure 响应 -> 是否成功 + 跳转地址
result = parse_usersure_response(raw)
# 5. 解析身份响应 -> 学校/人员/应用（含 nightattendance 的 AuthCode）
ident = parse_identity(envelope_data)
# 6. 解析签到点（candidates 可能多于一个）并构造签到请求体
config = parse_sign_position(sign_position_data)
sign_body = build_sign_in_body(
    lnglat=config.positions[0].lnglat, address=config.positions[0].address
)
```

## 错误模型

- `ParseError`：输入不符合已知形态（带字段名与 ≤120 字符片段摘要）；
- `SessionExpired`：信封 `code == 999`（会话失效，调用方必须重登）；
- 业务失败码（如 usersure `e001`）**作为数据返回**，不抛异常；
- `looks_like_challenge` 只检测风控/挑战页，**不提供任何绕过手段**——命中即应停止并人工介入。

## 路线图

后续版本规划：`inspector`（离线夹具/流量自检）与 `mock`（本地假上游），用于在不触网的前提下
端到端演练本库。

## 许可

MIT。规格与夹具来源见 `PROVENANCE.md`。
