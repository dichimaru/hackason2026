package db

import (
	"database/sql"
	"fmt"
	"log"
	"time"

	_ "github.com/go-sql-driver/mysql"

	"github.com/hackason2026/webapp-go/internal/config"
)

// MustOpen は接続できるまで最大30回リトライする。MySQL起動待ちのため。
func MustOpen(c config.Config) *sql.DB {
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true&charset=utf8mb4&loc=Local",
		c.DBUser, c.DBPass, c.DBHost, c.DBPort, c.DBName)
	var d *sql.DB
	var err error
	for i := 0; i < 30; i++ {
		d, err = sql.Open("mysql", dsn)
		if err == nil {
			if err = d.Ping(); err == nil {
				return d
			}
		}
		log.Printf("waiting for DB... (%d): %v", i, err)
		time.Sleep(2 * time.Second)
	}
	log.Fatalf("failed to connect db: %v", err)
	return nil
}
