import asyncio
from pathlib import Path

from openai import OpenAI
from ragas import Dataset, experiment
from ragas.llms import llm_factory
import pandas as pd
from ragas.metrics import DiscreteMetric

from cities_rag import answer_query, build_rag_graph
from config import get_chat_model, get_encoder


def load_dataset():
    dataset = Dataset(
        name="test_dataset",
        backend="local/csv",
        root_dir="evals",
    )

    data_samples = pd.read_csv("evals/questions.csv").to_dict(orient="records")

    for sample in data_samples:
        row = {"question": sample["question"], "grading_notes": sample["grading_notes"], "category": sample["category"]}
        dataset.append(row)

    # make sure to save it
    dataset.save()
    return dataset

my_metric = DiscreteMetric(
    name="correctness",
    prompt="Check if the response contains points mentioned from the grading notes. If they are similar return 'pass'. Otherwise, return 'fail'.\nResponse: {response} Grading Notes: {grading_notes}",
    allowed_values=["pass", "fail"],
)

rag_client = build_rag_graph()

_chat_model = get_chat_model()
llm = llm_factory(
    _chat_model.model_name,
    client=OpenAI(
        base_url=_chat_model.openai_api_base,
        api_key=_chat_model.openai_api_key.get_secret_value(),
    ),
)

@experiment()
async def run_experiment(row):
    response = rag_client.invoke({"query": row["question"]})

    score = my_metric.score(
        llm=llm,
        response=response,
        grading_notes=row["grading_notes"]
    )

    experiment_view = {
        **row,
        "response": response["answer"],
        "score": score.value,
        "log_file": response,
    }
    return experiment_view


async def main():
    dataset = load_dataset()
    print("dataset loaded successfully", dataset)

    experiment_results = await run_experiment.arun(dataset)
    print("Experiment completed successfully!")
    print("Experiment results:", experiment_results)

    # Save experiment results to CSV
    experiment_results.save()
    csv_path = Path(".") / "evals" / "experiments" / f"{experiment_results.name}.csv"
    print(f"\nExperiment results saved to: {csv_path.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())

