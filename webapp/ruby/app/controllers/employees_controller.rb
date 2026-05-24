class EmployeesController < ApplicationController
  def index
    employees = Employee.order(:id).pluck(:id, :name, :email, :department, :active)
    render json: employees.map { |id, name, email, department, active|
      { id: id, name: name, email: email, department: department, active: active == 1 || active == true }
    }
  end
end
