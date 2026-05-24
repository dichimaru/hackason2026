class Duty < ApplicationRecord
  belongs_to :employee
  belongs_to :area

  enum :status, { pending: "pending", done: "done", swapped: "swapped" }
end
