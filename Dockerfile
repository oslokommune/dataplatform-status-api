FROM public.ecr.aws/lambda/python:3.11

COPY event ${LAMBDA_TASK_ROOT}/event
COPY status ${LAMBDA_TASK_ROOT}/status
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

CMD ["set-me-in-serverless.yaml"]
