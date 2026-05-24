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
		api.GET("/employees", h.ListEmployees)
		api.GET("/areas", h.ListAreas)
		api.GET("/duties", h.ListDuties)
		api.POST("/duties/generate", h.GenerateDuties)
	}
	return r
}
