from typing import Sequence, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple, CheckpointMetadata, ChannelVersions
from pathlib import Path
import json
import pickle
import base64
import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.file_management import FileManagementToolkit

# ============ 1. 配置 ============
file_tools = FileManagementToolkit(root_dir='D:\\sd14\\ai-agent\\temp').get_tools()

load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")

qwen_llm = ChatOpenAI(
    model="qwen-plus",
    api_key=api_key,
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True,
    temperature=0.7,
)


# ============ 2. 自定义 Checkpoint Saver ============
class FileCheckpointSaver(BaseCheckpointSaver[str]):
    """
    自定义文件持久化 Checkpoint Saver

    目录结构：
    {base_dir}/
        └── {thread_id}/
            ├── {checkpoint_id}.json          # checkpoint 数据
            └── writes/                       # 增量数据（可选）
                └── {checkpoint_id}_{task_id}.json
    """

    def __init__(self, base_dir: str = './checkpoints'):
        super().__init__()
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        print(f'[FileSaver] 🚀 初始化完成，存储目录: {self.base_dir}')

    # ========== 辅助方法 ==========
    def _get_checkpoint_path(self, thread_id: str, checkpoint_id: str) -> str:
        """生成 checkpoint 文件路径"""
        dir_path = os.path.join(self.base_dir, str(thread_id))
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, f'{checkpoint_id}.json')

    def _serialize(self, data: Any) -> str:
        """序列化数据为 base64 字符串"""
        return base64.b64encode(pickle.dumps(data)).decode('utf-8')

    def _deserialize(self, data: str) -> Any:
        """反序列化 base64 字符串"""
        return pickle.loads(base64.b64decode(data))

    # ========== 核心方法 ==========
    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """
        获取 checkpoint（恢复记忆）

        执行流程：
        1. 从 config 提取 thread_id 和 checkpoint_id
        2. 检查目录是否存在
        3. 获取所有 checkpoint 文件
        4. 根据 checkpoint_id 或最新文件进行加载
        5. 反序列化并返回 CheckpointTuple
        """
        thread_id = config['configurable']['thread_id']
        checkpoint_id = config['configurable'].get('checkpoint_id', None)

        dir_path = os.path.join(self.base_dir, str(thread_id))

        # 检查目录是否存在
        if not os.path.exists(dir_path):
            print(f'[FileSaver] ℹ️ 目录不存在: {dir_path}')
            return None

        # 获取所有 checkpoint 文件
        checkpoint_files = list(Path(dir_path).glob('*.json'))
        if not checkpoint_files:
            print(f'[FileSaver] ℹ️ 没有 checkpoint 文件: {dir_path}')
            return None

        # 选择要加载的 checkpoint
        if checkpoint_id:
            target_file = Path(dir_path) / f'{checkpoint_id}.json'
            if not target_file.exists():
                print(f'[FileSaver] ⚠️ checkpoint 不存在: {checkpoint_id}')
                return None
            checkpoint_file_path = target_file
        else:
            # 获取最新的 checkpoint
            checkpoint_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            checkpoint_file_path = checkpoint_files[0]
            checkpoint_id = checkpoint_file_path.stem

        # 读取并反序列化
        with open(checkpoint_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        checkpoint = self._deserialize(data['checkpoint'])
        metadata = self._deserialize(data['metadata'])

        print(f'[FileSaver] ✅ 恢复记忆: {checkpoint_file_path}')

        return CheckpointTuple(
            config={
                'configurable': {
                    'thread_id': str(thread_id),
                    'checkpoint_id': checkpoint_id,
                }
            },
            checkpoint=checkpoint,
            metadata=metadata,
        )

    def put(
            self,
            config: RunnableConfig,
            checkpoint: CheckpointTuple,
            metadata: CheckpointMetadata,
            new_version: ChannelVersions,
    ) -> RunnableConfig:
        """
        存储 checkpoint（全量保存）

        执行流程：
        1. 提取 thread_id 和 checkpoint_id
        2. 生成存储路径
        3. 序列化 checkpoint 和 metadata
        4. 写入 JSON 文件
        """
        thread_id = config['configurable']['thread_id']
        checkpoint_id = checkpoint['id']
        checkpoint_path = self._get_checkpoint_path(str(thread_id), checkpoint_id)

        checkpoint_data = {
            'checkpoint': self._serialize(checkpoint),
            'metadata': self._serialize(metadata),
            'timestamp': datetime.now().isoformat(),
        }

        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

        print(f'[FileSaver] ✅ 已保存 checkpoint: {checkpoint_path}')
        return config

    def put_writes(
            self,
            config: RunnableConfig,
            writes: Sequence[tuple[str, Any]],
            task_id: str,
            task_path: str = "",
    ) -> None:
        """
        存储中间写入（增量数据）

        注意：此方法必须实现，即使为空实现
        """
        thread_id = config['configurable']['thread_id']
        checkpoint_id = config['configurable'].get('checkpoint_id', 'latest')

        # 可选的增量存储实现
        # 这里只记录日志，不实际存储
        print(f'[FileSaver] 📝 put_writes: {len(writes)} 条写入')

        # 如果需要存储增量数据，取消注释以下代码
        """
        writes_dir = os.path.join(self.base_dir, str(thread_id), 'writes')
        os.makedirs(writes_dir, exist_ok=True)

        writes_file = os.path.join(writes_dir, f'{checkpoint_id}_{task_id}.json')
        with open(writes_file, 'w', encoding='utf-8') as f:
            json.dump({
                'writes': writes,
                'task_id': task_id,
                'task_path': task_path,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        """


# ============ 3. 运行测试 ============
if __name__ == '__main__':
    # 使用文件持久化
    memory = FileCheckpointSaver(base_dir='D:\\sd14\\ai-agent\\temp\\checkpoints')

    agent = create_react_agent(
        model=qwen_llm,
        tools=file_tools,
        checkpointer=memory,
        debug=False,
    )

    config = RunnableConfig(configurable={'thread_id': 'user_123'})

    print("\n" + "=" * 60)
    print("🤖 开始对话（输入 'q' 退出）")
    print("=" * 60 + "\n")

    while True:
        user_input = input('👤 用户: ')
        if user_input.lower() == 'q':
            break

        try:
            res = agent.invoke(
                {'messages': [('user', user_input)]},
                config=config
            )
            # 提取 AI 回复
            ai_response = res['messages'][-1].content
            print(f'🤖 助理: {ai_response}\n')
        except Exception as e:
            print(f'❌ 错误: {e}\n')