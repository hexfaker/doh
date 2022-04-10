ssh-server:
    FROM golang:1.15-buster
    GIT CLONE --branch main https://github.com/okteto/remote.git /app
    WORKDIR /app

    RUN go mod download

    ENV COMMIT_SHA=${EARTHLY_GIT_HASH}
    RUN make

    SAVE ARTIFACT /app/remote AS LOCAL doh/bin/ssh-server
