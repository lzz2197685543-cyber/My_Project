from typing import Sequence, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple, CheckpointMetadata, ChannelVersions
from app.code_agent.model.qwen import qwen_llm
from app.code_agent.tools.file_tools import file_tools
from pathlib import Path
import json
import pickle
import base64
import os

"""
get_tuple    # 检查thread_id=1是否有历史checkpoint
put          # 保存初始状态
put_writes   # 保存用户输入消息
put          # 更新状态（包含用户消息）
put_writes   # 保存AI响应
put          # 更新最终状态（包含完整对话）
"""


class CheckpointSaver(BaseCheckpointSaver[str]):
    def __init__(self, base_dir: str = 'E:\\Ai_Agent\\temp\\checkpoint'):
        super().__init__()
        self.base_dir = base_dir

        os.makedirs(self.base_dir, exist_ok=True)

    def _get_checkpoint_path(self,thread_id,checkpoint_id):
        dir_path = os.path.join(self.base_dir, thread_id)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path,checkpoint_id+'.json')
        return file_path

    def _serialize_checkpoint(self,data):
        pickled=pickle.dumps(data)
        return base64.b64encode(pickled).decode()

    def _deserialize_data(self,data):
        decoded=base64.b64decode(data)
        return pickle.loads(decoded)

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Fetch a checkpoint tuple using the given configuration.

        Args:
            config: Configuration specifying which checkpoint to retrieve.

        Returns:
            The requested checkpoint tuple, or `None` if not found.
        """
        # 1.找到正确的checkpoint文件路径
        thread_id = config['configurable']['thread_id']
        checkpoint_id = config['configurable'].get('checkpoint_id', None)

        # 2.读取checkpoint文件内容
        # 如果没有指定checkpoint_id，获取最新的checkpoint
        dir_path = os.path.join(self.base_dir, str(thread_id))

        # 如果目录不存在或没有checkpoint文件，返回None
        if not os.path.exists(dir_path):
            return None

        checkpoint_files = list(Path(dir_path).glob('*.json'))
        if not checkpoint_files:
            return None

        checkpoint_files.sort(key=lambda x: x.stem, reverse=True)
        latest_checkpoint = checkpoint_files[0]
        checkpoint_id = latest_checkpoint.stem

        checkpoint_file_path = self._get_checkpoint_path(str(thread_id), checkpoint_id)

        # 3.对文件内容进行反序列化
        with open(checkpoint_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        checkpoint = self._deserialize_data(data['checkpoint'])
        metadata = self._deserialize_data(data['metadata'])

        # 4.返回checkpoint对象
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

    def put(self, config: RunnableConfig,
            checkpoint: CheckpointTuple,
            metadata: CheckpointMetadata,
            new_version: ChannelVersions,
            ) -> RunnableConfig:
        """Store a checkpoint with its configuration and metadata.

                        Args:
                            config: Configuration for the checkpoint.
                            checkpoint: The checkpoint to store.
                            metadata: Additional metadata for the checkpoint.
                            new_versions: New channel versions as of this write.

                        Returns:
                            RunnableConfig: Updated configuration after storing the checkpoint.

                """

        # 1.生成存储的 JSON 文件路径
        thread_id=config['configurable']['thread_id']
        checkpoint_id=checkpoint['id']
        checkpoint_path = self._get_checkpoint_path(thread_id,checkpoint_id)

        # 2.将 Checkpoint 进行序列化
        checkpoint_data={
            'checkpoint':self._serialize_checkpoint(checkpoint),
            'metadata':self._serialize_checkpoint(metadata),
        }

        # 3.将Checkpoint 存储到文件系统
        with open(checkpoint_path,'w',encoding='utf-8') as f:
            json.dump(checkpoint_data,f,indent=2,ensure_ascii=False)

        # 4.返回一个值
        # print('put')
        return config

    def put_writes(
            self,
            config: RunnableConfig,
            writes: Sequence[tuple[str, Any]],
            task_id: str,
            task_path: str = "",
    ) -> None:
        """Store intermediate writes linked to a checkpoint.

                Args:
                    config: Configuration of the related checkpoint.
                    writes: List of writes to store.
                    task_id: Identifier for the task creating the writes.
                    task_path: Path of the task creating the writes.
        """

        print('')


    # 实现异步的这get_put/put_writes/put方法
    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """异步获取 checkpoint - 直接调用同步方法"""
        return self.get_tuple(config)

    async def aput(self, config: RunnableConfig,
                   checkpoint: CheckpointTuple,
                   metadata: CheckpointMetadata,
                   new_version: ChannelVersions,
                   ) -> RunnableConfig:
        """异步存储 checkpoint - 直接调用同步方法"""
        return self.put(config, checkpoint, metadata, new_version)

    async def aput_writes(
            self,
            config: RunnableConfig,
            writes: Sequence[tuple[str, Any]],
            task_id: str,
            task_path: str = "",
    ) -> None:
        """异步存储中间写入 - 直接调用同步方法"""
        return self.put_writes(config, writes, task_id, task_path)


if __name__ == '__main__':
    memory = CheckpointSaver(base_dir='D:\\sd14\\ai-agent\\temp')

    agent = create_react_agent(
        model=qwen_llm,
        tools=file_tools,
        checkpointer=memory,
        debug=False,
    )
    config=RunnableConfig(configurable={'thread_id':2})
    while True:
        user_input=input('用户:')

        if user_input=='q':
            break

        res = agent.invoke({'messages': user_input}, config=config)
        print("助理：",res['message'][-1]['content'])

