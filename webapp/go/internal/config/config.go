package config

import "os"

type Config struct {
	DBHost string
	DBPort string
	DBUser string
	DBPass string
	DBName string
	Port   string
}

func Load() Config {
	return Config{
		DBHost: env("DB_HOST", "db"),
		DBPort: env("DB_PORT", "3306"),
		DBUser: env("DB_USER", "cleaning"),
		DBPass: env("DB_PASS", "cleaning"),
		DBName: env("DB_NAME", "cleaning"),
		Port:   env("PORT", "8080"),
	}
}

func env(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}
