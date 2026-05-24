class HealthController < ApplicationController
  def show
    ActiveRecord::Base.connection.execute("SELECT 1")
    render json: { status: "ok" }
  rescue => e
    render json: { status: "ng", error: e.message }, status: :internal_server_error
  end
end
