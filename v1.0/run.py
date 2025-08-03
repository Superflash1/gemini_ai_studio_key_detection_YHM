import argparse
import sys
from gemini_key_checker.main import process_keys

def main():
    """
    The main entry point for the Gemini Key Checker application.
    Parses command-line arguments and initiates the key checking process.
    """
    parser = argparse.ArgumentParser(
        description="批量检测 Google Gemini API 密钥的有效性。",
        epilog="可以直接提供密钥作为参数，或使用 -f/--file 从文件中加载。"
    )
    parser.add_argument(
        'keys',
        nargs='*',
        help="一个或多个要检测的 Gemini API 密钥。"
    )
    parser.add_argument(
        '-f', '--file',
        type=str,
        help="包含 API 密钥列表的文件路径（每行一个）。"
    )
    parser.add_argument(
        '-c', '--concurrency',
        type=int,
        default=100,
        help="并发检测的线程数（默认为 10）。"
    )
    parser.add_argument(
        '--proxy',
        type=str,
        default="http://127.0.0.1:7890",
        help="代理服务器地址（默认为 Clash 的 http://127.0.0.1:7890）。"
    )
    parser.add_argument(
        '--no-proxy',
        action='store_true',
        help="禁用代理，直接连接。"
    )

    args = parser.parse_args()

    keys_to_check = []
    
    # 从文件加载密钥
    if args.file:
        try:
            with open(args.file, 'r') as f:
                keys_from_file = [line.strip() for line in f if line.strip()]
                keys_to_check.extend(keys_from_file)
        except FileNotFoundError:
            print(f"[错误] 文件未找到: {args.file}")
            sys.exit(1)
        except Exception as e:
            print(f"[错误] 读取文件时出错: {e}")
            sys.exit(1)

    # 从命令行参数加载密钥
    if args.keys:
        keys_to_check.extend(args.keys)
    
    # 去重
    unique_keys = sorted(list(set(keys_to_check)))

    if not unique_keys:
        parser.print_help()
        sys.exit(0)

    # 确定代理设置
    proxy_url = None if args.no_proxy else args.proxy
    
    process_keys(unique_keys, args.concurrency, proxy_url)


if __name__ == "__main__":
    main() 