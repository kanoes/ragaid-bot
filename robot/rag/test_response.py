#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG问答系统测试脚本

这个脚本用于测试RAG系统的各个层次功能：
1. 触发层 (trigger_layer)：测试不同事件类型触发时的行为
2. 思考层 (thinking_layer)：测试知识检索和LLM集成
3. 决策层 (decision_layer)：测试输出简化
4. 完整测试：从输入到最终行动的整个流程
"""

import os
import sys
import argparse
import json

# 添加项目根目录到路径以便导入
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from robot.rag import RAGModule

# 默认知识库文件路径
DEFAULT_KNOWLEDGE_FILE = os.path.join(current_dir, "knowledge", "restaurant_rule.json")


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
    print("RAG系统分层测试")
    print("=" * 50)
    
    if not rag.is_ready():
        print("警告: 未加载知识库，将使用纯LLM回答")
    else:
        print(f"已成功加载知识库: {knowledge_file or DEFAULT_KNOWLEDGE_FILE}")
    
    while True:
        # 选择测试模式
        print("\n请选择测试模式:")
        print("1. 问答测试 (直接查询)")
        print("2. 思考层测试 (thinking_layer)")
        print("3. 触发层测试 (trigger_layer)")
        print("4. 决策接口测试 (make_decision)")
        print("q. 退出")
        
        mode = input("\n请选择 (1-4 或 q): ")
        if mode.lower() == 'q':
            break
            
        if mode == '1':
            # 问答测试
            query = input("\n请输入问题: ")
            if not query:
                continue
                
            use_rag = rag.is_ready()
            if rag.is_ready():
                choice = input("是否使用RAG增强回答? (y/n, 默认y): ").lower()
                use_rag = choice != 'n'
            
            print("\n正在思考中...")
            try:
                answer = rag.query_answer(query, use_rag=use_rag)
                print(f"\n回答: {answer}")
            except Exception as e:
                print(f"发生错误: {e}")
                
        elif mode == '2':
            # 思考层测试
            query = input("\n请输入问题: ")
            if not query:
                continue
                
            use_rag = rag.is_ready()
            if rag.is_ready():
                choice = input("是否使用RAG增强回答? (y/n, 默认y): ").lower()
                use_rag = choice != 'n'
            
            print("\n正在通过思考层处理...")
            try:
                raw_response, context_docs = rag.thinking_layer(query, use_rag=use_rag)
                print("\n思考层输出:")
                print(f"- 检索到的文档: {len(context_docs)} 条")
                for i, doc in enumerate(context_docs, 1):
                    print(f"  文档 {i}: {doc[:100]}..." if len(doc) > 100 else f"  文档 {i}: {doc}")
                print(f"\n- LLM原始响应:\n{raw_response}")
                
                # 测试决策层的处理结果
                action = rag.decision_layer(raw_response)
                print(f"\n- 决策层简化结果: {action}")
                
            except Exception as e:
                print(f"发生错误: {e}")
                
        elif mode == '3':
            # 触发层测试
            print("\n请选择事件类型:")
            print("1. 路径规划事件 (plan)")
            print("2. 障碍处理事件 (obstacle)")
            
            event_choice = input("请选择 (1-2): ")
            if event_choice == '1':
                event_type = 'plan'
                context = {
                    'robot_id': int(input("机器人ID (默认1): ") or 1),
                    'start': eval(input("起点坐标 (x,y) 格式，默认(0,0): ") or "(0,0)"),
                    'goal': eval(input("目标坐标 (x,y) 格式，默认(10,10): ") or "(10,10)")
                }
            elif event_choice == '2':
                event_type = 'obstacle'
                context = {
                    'robot_id': int(input("机器人ID (默认1): ") or 1),
                    'position': eval(input("当前位置 (x,y) 格式，默认(5,5): ") or "(5,5)"),
                    'goal': eval(input("目标位置 (x,y) 格式，默认(10,10): ") or "(10,10)"),
                    'obstacle': eval(input("障碍位置 (x,y) 格式，默认(6,6): ") or "(6,6)")
                }
            else:
                print("无效选择")
                continue
                
            print(f"\n正在通过触发层处理 {event_type} 事件...")
            try:
                result = rag.trigger_layer(event_type, context)
                print("\n触发层结果:")
                print(f"- 动作: {result['action']}")
                print(f"- 是否使用上下文: {result['context_used']}")
                print(f"- 检索到的文档数: {len(result['context_docs'])}")
                print(f"- LLM原始响应:\n{result['raw_response']}")
            except Exception as e:
                print(f"发生错误: {e}")
                
        elif mode == '4':
            # 决策接口测试
            print("\n请选择情境类型:")
            print("1. 路径规划 (plan)")
            print("2. 障碍处理 (obstacle)")
            
            situation_choice = input("请选择 (1-2): ")
            if situation_choice == '1':
                situation_type = 'plan'
                kwargs = {
                    'robot_id': int(input("机器人ID (默认1): ") or 1),
                    'start': eval(input("起点坐标 (x,y) 格式，默认(0,0): ") or "(0,0)"),
                    'goal': eval(input("目标坐标 (x,y) 格式，默认(10,10): ") or "(10,10)")
                }
            elif situation_choice == '2':
                situation_type = 'obstacle'
                kwargs = {
                    'robot_id': int(input("机器人ID (默认1): ") or 1),
                    'position': eval(input("当前位置 (x,y) 格式，默认(5,5): ") or "(5,5)"),
                    'goal': eval(input("目标位置 (x,y) 格式，默认(10,10): ") or "(10,10)"),
                    'context': eval(input("障碍位置 (x,y) 格式，默认(6,6): ") or "(6,6)")
                }
            else:
                print("无效选择")
                continue
            
            print(f"\n正在测试决策接口，情境: {situation_type}...")
            try:
                action = rag.make_decision(situation_type, **kwargs)
                print(f"\n决策结果: {action}")
            except Exception as e:
                print(f"发生错误: {e}")
        else:
            print("无效选择")


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
                # 使用思考层测试
                raw_response, docs = rag.thinking_layer(question, use_rag=use_rag)
                print(f"检索到的文档数: {len(docs)}")
                print(f"答案: {raw_response}\n{'-'*30}")
            except Exception as e:
                print(f"错误: {e}\n{'-'*30}")


def test_scenarios(knowledge_file=None, api_key=None):
    """
    测试不同场景下的RAG响应
    
    Args:
        knowledge_file: 知识库文件路径
        api_key: OpenAI API密钥
    """
    # 初始化RAG模块
    rag = RAGModule(
        api_key=api_key,
        knowledge_file=knowledge_file or DEFAULT_KNOWLEDGE_FILE,
    )
    
    print("\n===== 场景测试 =====")
    
    # 障碍物情境
    obstacle_scenarios = [
        {
            "name": "前方拥堵",
            "robot_id": 1,
            "position": (5, 5),
            "goal": (10, 10),
            "obstacle": (6, 6)
        },
        {
            "name": "死胡同",
            "robot_id": 1,
            "position": (2, 3),
            "goal": (2, 1),
            "obstacle": (2, 2)
        }
    ]
    
    # 规划情境
    plan_scenarios = [
        {
            "name": "长距离路径",
            "robot_id": 1,
            "start": (1, 1),
            "goal": (20, 20)
        },
        {
            "name": "穿过拥挤区域",
            "robot_id": 1,
            "start": (2, 2),
            "goal": (8, 8)
        }
    ]
    
    # 测试障碍物情境
    print("\n【障碍物情境测试】")
    for scenario in obstacle_scenarios:
        print(f"\n场景: {scenario['name']}")
        try:
            result = rag.trigger_layer('obstacle', scenario)
            print(f"- 建议动作: {result['action']}")
            print(f"- LLM响应: {result['raw_response'][:150]}..." if len(result['raw_response']) > 150 else f"- LLM响应: {result['raw_response']}")
        except Exception as e:
            print(f"错误: {e}")
    
    # 测试规划情境
    print("\n【规划情境测试】")
    for scenario in plan_scenarios:
        print(f"\n场景: {scenario['name']}")
        try:
            result = rag.trigger_layer('plan', scenario)
            print(f"- 建议: {result['action']}")
            print(f"- LLM响应: {result['raw_response'][:150]}..." if len(result['raw_response']) > 150 else f"- LLM响应: {result['raw_response']}")
        except Exception as e:
            print(f"错误: {e}")


def export_test_results(knowledge_file=None, api_key=None, output_file="rag_test_results.json"):
    """
    运行测试并导出结果到JSON文件
    
    Args:
        knowledge_file: 知识库文件路径
        api_key: OpenAI API密钥
        output_file: 输出文件路径
    """
    # 初始化RAG模块
    rag = RAGModule(
        api_key=api_key,
        knowledge_file=knowledge_file or DEFAULT_KNOWLEDGE_FILE,
    )
    
    print("\n===== 导出测试结果 =====")
    
    # 问答测试集
    test_questions = [
        "什么是RAG技术？",
        "如何处理餐厅中的拥堵问题？",
        "机器人应该如何避让移动障碍物？"
    ]
    
    # 场景测试集
    test_scenarios = {
        "obstacle": [
            {
                "name": "前方拥堵",
                "context": {
                    "robot_id": 1,
                    "position": (5, 5),
                    "goal": (10, 10),
                    "obstacle": (6, 6)
                }
            }
        ],
        "plan": [
            {
                "name": "多桌送餐路径规划",
                "context": {
                    "robot_id": 1,
                    "start": (0, 0),
                    "goal": (10, 10)
                }
            }
        ]
    }
    
    # 收集结果
    results = {
        "questions": [],
        "scenarios": {
            "obstacle": [],
            "plan": []
        }
    }
    
    # 问答测试
    print("\n进行问答测试...")
    for question in test_questions:
        print(f"测试问题: {question}")
        try:
            # 测试思考层
            raw_response, docs = rag.thinking_layer(question, use_rag=True)
            
            result = {
                "question": question,
                "docs_count": len(docs),
                "docs": [doc[:200] + "..." if len(doc) > 200 else doc for doc in docs],
                "response": raw_response,
                "simplified": rag.decision_layer(raw_response)
            }
            results["questions"].append(result)
        except Exception as e:
            print(f"错误: {e}")
            results["questions"].append({
                "question": question,
                "error": str(e)
            })
    
    # 场景测试
    print("\n进行场景测试...")
    # 障碍场景
    for scenario in test_scenarios["obstacle"]:
        print(f"测试障碍场景: {scenario['name']}")
        try:
            result = rag.trigger_layer('obstacle', scenario['context'])
            scenario_result = {
                "name": scenario["name"],
                "context": scenario["context"],
                "action": result["action"],
                "raw_response": result["raw_response"],
                "context_docs": [doc[:200] + "..." if len(doc) > 200 else doc for doc in result["context_docs"]]
            }
            results["scenarios"]["obstacle"].append(scenario_result)
        except Exception as e:
            print(f"错误: {e}")
            results["scenarios"]["obstacle"].append({
                "name": scenario["name"],
                "error": str(e)
            })
    
    # 规划场景
    for scenario in test_scenarios["plan"]:
        print(f"测试规划场景: {scenario['name']}")
        try:
            result = rag.trigger_layer('plan', scenario['context'])
            scenario_result = {
                "name": scenario["name"],
                "context": scenario["context"],
                "action": result["action"],
                "raw_response": result["raw_response"],
                "context_docs": [doc[:200] + "..." if len(doc) > 200 else doc for doc in result["context_docs"]]
            }
            results["scenarios"]["plan"].append(scenario_result)
        except Exception as e:
            print(f"错误: {e}")
            results["scenarios"]["plan"].append({
                "name": scenario["name"],
                "error": str(e)
            })
    
    # 导出结果
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n测试结果已导出至: {output_file}")
    except Exception as e:
        print(f"导出结果时发生错误: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='RAG系统分层测试工具')
    parser.add_argument('--knowledge', '-k', 
                        help=f'知识库JSON文件路径 (默认: {DEFAULT_KNOWLEDGE_FILE})',
                        default=None)
    parser.add_argument('--api-key', 
                        help='OpenAI API密钥 (可选，默认从环境变量读取)',
                        default=None)
    parser.add_argument('--mode', '-m',
                        help='测试模式: cli (交互式), batch (批处理), scenarios (场景测试), export (导出测试结果)',
                        choices=['cli', 'batch', 'scenarios', 'export'],
                        default='cli')
    parser.add_argument('--output', '-o',
                        help='导出模式下的输出文件路径',
                        default='rag_test_results.json')
    
    args = parser.parse_args()
    
    if args.mode == 'cli':
        run_cli_test(args.knowledge, args.api_key)
    elif args.mode == 'batch':
        run_test_batch(args.knowledge, args.api_key)
    elif args.mode == 'scenarios':
        test_scenarios(args.knowledge, args.api_key)
    elif args.mode == 'export':
        export_test_results(args.knowledge, args.api_key, args.output)


if __name__ == "__main__":
    main() 