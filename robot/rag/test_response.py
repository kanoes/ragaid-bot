#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG问答系统测试脚本

这个脚本用于测试RAG系统的问答功能。它允许用户：
1. 输入问题
2. 选择是否使用RAG增强回答
3. 获取LLM回答
"""

import os
import sys
import argparse

# 添加项目根目录到路径以便导入
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from robot.rag import RAGModule

# 默认知识库文件路径
DEFAULT_KNOWLEDGE_FILE = os.path.join(current_dir, "knowledge", "test_knowledge.json")


def run_cli_test(knowledge_file=None, api_key=None):
    """
    运行命令行测试界面
    
    Args:
        knowledge_file: 知识库文件路径
        api_key: OpenAI API密钥
    """
    # 初始化RAG模块
    rag = RAGModule(
        api_key=api_key,
        knowledge_file=knowledge_file or DEFAULT_KNOWLEDGE_FILE,
    )
    
    print("=" * 50)
    print("RAG问答系统测试")
    print("=" * 50)
    
    if not rag.is_ready():
        print("警告: 未加载知识库，将使用纯LLM回答")
    else:
        print(f"已成功加载知识库: {knowledge_file or DEFAULT_KNOWLEDGE_FILE}")
    
    while True:
        # 获取用户问题
        query = input("\n请输入问题 (输入'q'退出): ")
        if query.lower() in ('q', 'quit', 'exit'):
            break
            
        # 确定是否使用RAG
        use_rag = rag.is_ready()
        if rag.is_ready():
            choice = input("是否使用RAG增强回答? (y/n, 默认y): ").lower()
            use_rag = choice != 'n'
        
        print("\n正在思考中...")
        try:
            # 获取回答
            answer = rag.query_answer(query, use_rag=use_rag)
            print(f"\n回答: {answer}")
        except Exception as e:
            print(f"发生错误: {e}")


def run_test_batch(knowledge_file=None, api_key=None):
    """
    运行一组测试问题
    
    Args:
        knowledge_file: 知识库文件路径
        api_key: OpenAI API密钥
    """
    # 初始化RAG模块
    rag = RAGModule(
        api_key=api_key,
        knowledge_file=knowledge_file or DEFAULT_KNOWLEDGE_FILE,
    )
    
    print("\n===== 测试问题批处理 =====")
    
    # 测试问题
    test_questions = [
        "什么是Python语言？",
        "RAG技术是什么？",
        "FAISS是做什么用的？",
        "深度学习和机器学习有什么区别？",
        "解释一下向量数据库的用途"
    ]
    
    # 测试有RAG和无RAG两种情况
    for use_rag in [True, False]:
        mode = "使用RAG" if use_rag else "不使用RAG"
        print(f"\n\n【{mode}模式测试】")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n问题{i}: {question}")
            try:
                answer = rag.query_answer(question, use_rag=use_rag)
                print(f"回答: {answer}\n{'-'*30}")
            except Exception as e:
                print(f"错误: {e}\n{'-'*30}")


def compare_responses(knowledge_file=None, api_key=None):
    """
    比较同一问题有无RAG的回答差异
    
    Args:
        knowledge_file: 知识库文件路径
        api_key: OpenAI API密钥
    """
    # 初始化RAG模块
    rag = RAGModule(
        api_key=api_key,
        knowledge_file=knowledge_file or DEFAULT_KNOWLEDGE_FILE,
    )
    
    if not rag.is_ready():
        print("警告: 未加载知识库，无法进行对比测试")
        return
    
    print("\n===== RAG vs 非RAG对比测试 =====")
    
    # 测试问题
    question = input("请输入要对比测试的问题: ")
    
    # 不使用RAG的回答
    print("\n【不使用RAG】")
    try:
        answer_without_rag = rag.query_answer(question, use_rag=False)
        print(f"回答: {answer_without_rag}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 使用RAG的回答
    print("\n【使用RAG】")
    try:
        answer_with_rag = rag.query_answer(question, use_rag=True)
        print(f"回答: {answer_with_rag}")
    except Exception as e:
        print(f"错误: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='RAG问答系统测试')
    parser.add_argument('--knowledge', '-k', 
                        help=f'知识库JSON文件路径 (默认: {DEFAULT_KNOWLEDGE_FILE})',
                        default=None)
    parser.add_argument('--api-key', 
                        help='OpenAI API密钥 (可选，默认从环境变量读取)',
                        default=None)
    parser.add_argument('--mode', '-m',
                        help='测试模式: cli (交互式), batch (批处理), compare (对比)',
                        choices=['cli', 'batch', 'compare'],
                        default='cli')
    
    args = parser.parse_args()
    
    if args.mode == 'cli':
        run_cli_test(args.knowledge, args.api_key)
    elif args.mode == 'batch':
        run_test_batch(args.knowledge, args.api_key)
    elif args.mode == 'compare':
        compare_responses(args.knowledge, args.api_key)


if __name__ == "__main__":
    main() 