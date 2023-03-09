FROM public.ecr.aws/docker/library/alpine:3.17.2

ENV USER_NAME app
ENV USER_UID 1000

ENV GROUP_NAME app
ENV GROUP_GID 1000

ENV WORKDIR /app

WORKDIR $WORKDIR

RUN addgroup -g $GROUP_GID $GROUP_NAME && \
    adduser -D -u $USER_UID -G $GROUP_NAME $USER_NAME && \
    chown -R $USER_NAME:$GROUP_NAME .

USER $USER_NAME

COPY --chown=app:app --chmod=755 ./server ./
COPY --chown=app:app --chmod=755 ./entrypoint.sh ./

ENTRYPOINT ["sh", "-c",  "./entrypoint.sh &> /app/log/app.log"]
