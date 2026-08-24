from langchain_core.prompts import PromptTemplate,ChatPromptTemplate,ChatMessagePromptTemplate,FewShotPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

llm=ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True
)

example_template='输入：{input}\n输出：{output}'

examples=[
    {'input':'将Hello翻译成中文','output':'你好'},
    {'input':'将tool翻译成中文','output':'工具'},
]

few_shot_template=FewShotPromptTemplate(
    examples=examples,
    example_prompt=PromptTemplate.from_template(example_template),
    prefix='请将以下英文翻译成中文:',
    suffix="输入：{text}\n输出:",
    input_variables=['text']
)

print(few_shot_template)

prompt=few_shot_template.format(text='freedom')
print(prompt)

# 链式调用
chain=few_shot_template | llm

resp=chain.stream(input={'text':'freedom'})

for chunk in resp:
    print(chunk.content,end='')