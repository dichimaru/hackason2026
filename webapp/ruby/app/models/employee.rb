class Employee < ApplicationRecord
  has_many :duties, dependent: :restrict_with_exception

  scope :active, -> { where(active: true) }
end
