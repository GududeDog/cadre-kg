"""
测试 Qwen API (proxy/openai) 连通性
用法:
    python test_qwen_api.py                          # 默认测试
    python test_qwen_api.py --verbose                 # 显示完整响应
    python test_qwen_api.py --prompt "你好"           # 自定义提示词
"""
import argparse
import json
import sys
import time
from openai import OpenAI

API_KEY = "43F2FBB5055A7CDDCD082D740B0475E0"
BASE_URL = "http://41.0.0.114:8088/lm/v2"
MODEL = "qwen"


def test_qwen(prompt: str = None, verbose: bool = False):
    if prompt is None:
        prompt = "请用一句话介绍你自己"

    print(f"API 端点: {BASE_URL}/chat/completions")
    print(f"Model: {MODEL}")
    print(f"Prompt: {prompt}")
    print("-" * 50)

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    # 1. 连接测试
    print("[1/3] 连接测试 ...", end=" ", flush=True)
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.1,
        )
        elapsed = time.time() - t0
        print(f"OK ({(elapsed):.1f}s)")
    except Exception as e:
        print(f"失败: {e}")
        return False

    # 2. 响应解析
    print("[2/3] 响应解析 ...")
    content = resp.choices[0].message.content
    usage = getattr(resp, "usage", None)
    print(f"  回复: {content[:200]}")
    if usage:
        print(f"  tokens: {usage.total_tokens} (prompt {usage.prompt_tokens}, completion {usage.completion_tokens})")

    # 3. JSON 格式测试（模拟抽取场景）
    print("[3/3] JSON 格式测试 ...", end=" ", flush=True)
    json_prompt = """从以下文本中提取实体，以JSON格式返回：
文本：001同志现任南磨房乡党委书记。

{"entities": [{"type": "Cadre", "name": "001"}, {"type": "Position", "name": "南磨房乡党委书记"}], "relations": [], "tags": []}"""

    # Actually just test if the model can output JSON
    json_prompt_short = """从文本中提取实体，返回JSON：
文本：001同志现任南磨房乡党委书记。
输出格式：{"entities": [{"type": "Cadre", "name": "001"}]}"""

    try:
        resp2 = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": json_prompt_short}],
            max_tokens=200,
            temperature=0.1,
        )
        content2 = resp2.choices[0].message.content
        # try to parse as JSON
        try:
            parsed = json.loads(content2.strip().removeprefix("```json").removesuffix("```").strip())
            print(f"OK (valid JSON, {len(parsed.get('entities',[]))} entities)")
            if verbose:
                print(f"  {json.dumps(parsed, ensure_ascii=False, indent=2)}")
        except json.JSONDecodeError:
            print(f"非JSON格式回复:")
            print(f"  {content2[:200]}")
    except Exception as e:
        print(f"请求失败: {e}")

    print("-" * 50)
    print("测试完成.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Qwen API 连通性测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示完整响应")
    parser.add_argument("--prompt", "-p", type=str, default=None, help="自定义提示词")
    args = parser.parse_args()

    success = test_qwen(prompt=args.prompt, verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
