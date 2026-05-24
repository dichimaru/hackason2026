# 翌週5営業日 × 全エリア の当番を、社員からランダム公平抽選で生成。
class DutyGenerator
  class EmptyError < StandardError; end

  def generate
    emp_ids  = Employee.active.pluck(:id).shuffle
    area_ids = Area.pluck(:id)
    raise EmptyError, "employees or areas is empty" if emp_ids.empty? || area_ids.empty?

    created = 0
    idx = 0
    Duty.transaction do
      (7..11).each do |day|
        date = Date.current + day
        area_ids.each do |area_id|
          Duty.create!(
            employee_id:    emp_ids[idx % emp_ids.size],
            area_id:        area_id,
            scheduled_date: date,
            status:         "pending",
          )
          idx += 1
          created += 1
        end
      end
    end
    created
  end
end
