package db

import (
	"database/sql"
	"fmt"
	"log"
	"time"

	"gorm.io/driver/mysql"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"github.com/hackason2026/webapp-go/internal/config"
)

// MustOpen は接続できるまで最大30回リトライする。MySQL起動待ちのため。
//
// テーブル定義は webapp/sql/0_schema.sql を正とするので AutoMigrate は呼ばない。
// GORM に定義を作らせると SQL 側と二重管理になる。
func MustOpen(c config.Config) *gorm.DB {
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true&charset=utf8mb4&loc=Local",
		c.DBUser, c.DBPass, c.DBHost, c.DBPort, c.DBName)
	cfg := &gorm.Config{
		// 発行SQLを全部見たいときは logger.Info に上げる。
		Logger: logger.Default.LogMode(logger.Warn),
	}

	var err error
	for i := 0; i < 30; i++ {
		var gdb *gorm.DB
		if gdb, err = gorm.Open(mysql.Open(dsn), cfg); err == nil {
			var conn *sql.DB
			if conn, err = gdb.DB(); err == nil {
				if err = conn.Ping(); err == nil {
					return gdb
				}
			}
		}
		log.Printf("waiting for DB... (%d): %v", i, err)
		time.Sleep(2 * time.Second)
	}
	log.Fatalf("failed to connect db: %v", err)
	return nil
}
