import concurrent.futures
from tqdm import tqdm
from .checker import check_key

def process_keys(keys: list[str], concurrency: int, proxy_url: str = None):
    """
    Processes a list of API keys concurrently and saves the results to files.

    Args:
        keys: A list of API keys to check.
        concurrency: The number of concurrent threads to use.
        proxy_url: Proxy server URL. If None, no proxy will be used.
    """
    valid_keys = []
    invalid_keys = []
    
    proxy_info = f"，代理: {proxy_url}" if proxy_url else "，无代理"
    print(f"开始检测 {len(keys)} 个密钥，并发数: {concurrency}{proxy_info}...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_key = {executor.submit(check_key, key, proxy_url): key for key in keys}
        
        with tqdm(total=len(keys), desc="检测进度", unit="key") as pbar:
            for future in concurrent.futures.as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    is_valid, message = future.result()
                    # 为了安全，只显示部分密钥
                    short_key = f"{key[:7]}...{key[-4:]}"
                    if is_valid:
                        valid_keys.append(key)
                        pbar.set_postfix_str(f"✅ {short_key} - {message}", refresh=True)
                    else:
                        invalid_keys.append(f"{key} # {message}")
                        pbar.set_postfix_str(f"❌ {short_key} - {message}", refresh=True)
                except Exception as exc:
                    invalid_keys.append(f"{key} # ERROR: {exc}")
                    pbar.set_postfix_str(f"💥 {short_key} - 发生异常: {exc}", refresh=True)
                pbar.update(1)

    # 保存结果到文件
    try:
        with open('valid_keys.txt', 'w') as f:
            for key in valid_keys:
                f.write(f"{key}\n")
        
        with open('invalid_keys.txt', 'w') as f:
            for key_info in invalid_keys:
                f.write(f"{key_info}\n")
    except IOError as e:
        print(f"\n[错误] 写入结果文件失败: {e}")

    # 打印最终总结
    print("\n" + "="*30)
    print("检测完成！")
    print(f"  - ✅ 有效密钥: {len(valid_keys)}")
    print(f"  - ❌ 无效/错误密钥: {len(invalid_keys)}")
    print(f"结果已保存至 'valid_keys.txt' 和 'invalid_keys.txt'")
    print("="*30) 