FROM public.ecr.aws/lambda/python:3.11

COPY event ${LAMBDA_TASK_ROOT}/event
COPY status ${LAMBDA_TASK_ROOT}/status
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

RUN yum install shadow-utils -y
RUN /sbin/groupadd -r app
RUN /sbin/useradd -r -g app app
RUN chown -R app:app ${LAMBDA_TASK_ROOT}
USER app

CMD ["set-me-in-serverless.yaml"]
