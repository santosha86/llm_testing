from langchain_experimental.agents.agent_toolkits.pandas.base import create_pandas_dataframe_agent
import pandas as pd
from pathlib import Path
from .utils import model


csv_file_path = Path(__file__).parent.parent / 'vehicle_durations_with_driver_ids.csv'
tabular_data = pd.read_csv(csv_file_path)

def generate_context_prompt(df):
    context = "You are working with multiple dataframes. Here's a summary of the data:\n\n"
    #for name, df in dataframes.items():
    context += "Dataframe SSPC Data':\n"
    context += f"- Shape: {df.shape}\n"
    context += f"- Columns: {', '.join(df.columns)}\n\n"
    context += "Please refer to the dataframes by their names when answering questions.\n"
    context += "Now, please answer the following question about the data:\n\n"
    return context

pandas_df_agent = create_pandas_dataframe_agent(
    model,
    tabular_data,
    verbose=True,
    #handle_parsing_errors=True,
    allow_dangerous_code=True,
    agent_type="tool-calling"
)
# context_prompt = generate_context_prompt(tabular_data)
# prompt = "ما هو power plant desc for this waybill 1-24-0052638"
# full_prompt = context_prompt + prompt

# response = pandas_df_agent.invoke(full_prompt)

#print(response['output'])