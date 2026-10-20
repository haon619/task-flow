import { isFiltering, NO_FILTERS } from '../filter'
import type { Filters, StatusFilter } from '../filter'
import { STATUSES } from '../types'

interface Props {
  filters: Filters
  onChange: (filters: Filters) => void
}

function FilterBar({ filters, onChange }: Props) {
  return (
    <div className="filter-bar">
      <input
        type="search"
        aria-label="검색"
        placeholder="제목·설명 검색"
        value={filters.query}
        onChange={(e) => onChange({ ...filters, query: e.target.value })}
      />
      <select
        aria-label="상태 필터"
        value={filters.status}
        onChange={(e) =>
          onChange({ ...filters, status: e.target.value as StatusFilter })
        }
      >
        <option value="ALL">모든 상태</option>
        {STATUSES.map(({ value, label }) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
      {isFiltering(filters) && (
        <button type="button" onClick={() => onChange(NO_FILTERS)}>
          필터 지우기
        </button>
      )}
    </div>
  )
}

export default FilterBar
