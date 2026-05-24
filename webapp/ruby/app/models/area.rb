class Area < ApplicationRecord
  has_many :duties, dependent: :restrict_with_exception
end
