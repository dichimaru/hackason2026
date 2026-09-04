package router

import (
	"github.com/gin-gonic/gin"

	"github.com/hackason2026/webapp-go/internal/handler"
)

func New(h *handler.Handler) *gin.Engine {
	r := gin.Default() // Logger + Recovery 同梱

	api := r.Group("/api")
	{
		api.GET("/health", h.Health)
		api.GET("/people", h.ListEmployees)
		api.GET("/tasks", h.ListAreas)
		api.GET("/lottery-results", h.ListDuties)
		api.POST("/lottery-results/generate", h.GenerateDuties)
	}
	return r
}
