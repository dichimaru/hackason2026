class DutiesController < ApplicationController
  def index
    duties = Duty
      .joins(:employee, :area)
      .order(:scheduled_date, "areas.id")
      .pluck(
        "duties.id", "duties.employee_id", "employees.name",
        "duties.area_id", "areas.name",
        "duties.scheduled_date", "duties.status",
      )
    render json: duties.map { |id, emp_id, emp_name, area_id, area_name, date, status|
      {
        id: id,
        employee_id: emp_id,
        employee_name: emp_name,
        area_id: area_id,
        area_name: area_name,
        scheduled_date: date.to_s,
        status: status,
      }
    }
  end

  def generate
    created = DutyGenerator.new.generate
    render json: { created: created }
  rescue DutyGenerator::EmptyError => e
    render json: { error: e.message }, status: :bad_request
  end
end
