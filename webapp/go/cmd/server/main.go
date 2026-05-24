package main

import (
	"log"

	"github.com/hackason2026/webapp-go/internal/config"
	"github.com/hackason2026/webapp-go/internal/db"
	"github.com/hackason2026/webapp-go/internal/handler"
	"github.com/hackason2026/webapp-go/internal/router"
)

func main() {
	cfg := config.Load()
	conn := db.MustOpen(cfg)
	h := handler.New(conn)
	r := router.New(h)

	addr := ":" + cfg.Port
	log.Printf("listening on %s", addr)
	if err := r.Run(addr); err != nil {
		log.Fatal(err)
	}
}
