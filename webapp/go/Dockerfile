FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY go.mod ./
COPY cmd ./cmd
COPY internal ./internal
RUN go mod tidy && CGO_ENABLED=0 go build -o /out/webapp ./cmd/server

FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /app
COPY --from=builder /out/webapp /app/webapp
EXPOSE 8080
USER nonroot:nonroot
ENTRYPOINT ["/app/webapp"]
