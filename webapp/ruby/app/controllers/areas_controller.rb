class AreasController < ApplicationController
  def index
    render json: Area.order(:id).select(:id, :name, :description)
  end
end
