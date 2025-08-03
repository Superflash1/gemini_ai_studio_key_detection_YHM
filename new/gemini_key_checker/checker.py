import google.generativeai as genai
from google.api_core import exceptions
import requests
import os
import json

def check_key(api_key: str, proxy_url: str = None, use_proxy: bool = True, api_url: str = None) -> tuple[bool, str]:
    """
    Checks the validity of a Gemini API key by trying to list models.

    Args:
        api_key: The Gemini API key to check.
        proxy_url: Proxy server URL. Only used if use_proxy is True.
        use_proxy: Whether to use proxy. Defaults to True.
        api_url: Custom API endpoint URL. If empty/None, uses Google official API.

    Returns:
        A tuple containing a boolean (True if valid, False otherwise)
        and a status message.
    """
    if not isinstance(api_key, str) or not api_key.strip():
        return False, "INVALID: Key is empty or not a string."

    # 设置代理
    if use_proxy and proxy_url:
        os.environ['HTTP_PROXY'] = proxy_url
        os.environ['HTTPS_PROXY'] = proxy_url
    else:
        # 清除代理设置（如果之前设置过）
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)

    # 如果提供了自定义API URL，使用requests库
    if api_url and api_url.strip():
        return _check_key_with_custom_url(api_key, api_url.strip(), use_proxy, proxy_url)
    else:
        # 使用原有的Google genai SDK
        return _check_key_with_genai_sdk(api_key)

def _check_key_with_custom_url(api_key: str, api_url: str, use_proxy: bool, proxy_url: str) -> tuple[bool, str]:
    """使用自定义API URL检测密钥"""
    try:
        # 设置请求代理
        proxies = {}
        if use_proxy and proxy_url:
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        
        # 构建请求头
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # 如果URL不包含完整路径，尝试添加标准的模型列表端点
        if not api_url.endswith('/models'):
            if api_url.endswith('/'):
                api_url = api_url + 'v1/models'
            else:
                api_url = api_url + '/v1/models'
        
        # 发送请求
        response = requests.get(
            api_url,
            headers=headers,
            proxies=proxies if proxies else None,
            timeout=10
        )
        
        # 检查响应
        if response.status_code == 200:
            # 尝试解析JSON响应，确保是有效的API响应
            try:
                data = response.json()
                if 'models' in data or 'data' in data or isinstance(data, list):
                    return True, "VALID"
                else:
                    return False, f"INVALID: Unexpected API response format"
            except json.JSONDecodeError:
                return False, f"INVALID: Invalid JSON response from API"
        elif response.status_code == 401:
            return False, "INVALID: Authentication failed - Invalid API key"
        elif response.status_code == 403:
            return False, "INVALID: Permission denied - API key lacks required permissions"
        elif response.status_code == 404:
            return False, f"ERROR: API endpoint not found - {api_url}"
        else:
            return False, f"ERROR: API request failed with status {response.status_code}"
            
    except requests.exceptions.ProxyError:
        return False, f"ERROR: Proxy connection failed - {proxy_url}"
    except requests.exceptions.ConnectTimeout:
        return False, f"ERROR: Connection timeout to {api_url}"
    except requests.exceptions.ConnectionError:
        return False, f"ERROR: Failed to connect to {api_url}"
    except Exception as e:
        return False, f"ERROR: An unexpected error occurred - {str(e)}"

def _check_key_with_genai_sdk(api_key: str) -> tuple[bool, str]:
    """使用Google genai SDK检测密钥（原有逻辑）"""
    try:
        # Each key needs its own client instance for thread safety
        # Although genai.configure is global, reconfiguring it per check
        # in a threaded environment is necessary.
        genai.configure(api_key=api_key)
        
        # The list_models() call is what actually triggers the API request.
        # We iterate through it to ensure the request is made.
        # Set a 10-second timeout for the API request.
        list(genai.list_models(request_options={'timeout': 10}))
        
        return True, "VALID"
    except exceptions.PermissionDenied as e:
        # This is the most common error for an invalid or revoked key.
        return False, f"INVALID: Permission Denied - {e.message}"
    except exceptions.InvalidArgument as e:
        # This can happen if the key format is wrong.
        return False, f"INVALID: Invalid Argument - {e.message}"
    except exceptions.GoogleAPICallError as e:
        # A catch-all for other Google API errors.
        return False, f"INVALID: API Call Error - {e.message}"
    except Exception as e:
        # Catch other potential exceptions (e.g., network issues)
        return False, f"ERROR: An unexpected error occurred - {str(e)}" 