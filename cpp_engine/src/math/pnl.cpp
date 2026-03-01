#include "munnir_engine/pnl.hpp"

namespace munnir {

int64_t calculate_pnl(int64_t entry_price_cents,
                      int64_t current_price_cents,
                      int64_t quantity) {
    return (current_price_cents - entry_price_cents) * quantity;
}

double calculate_pnl_percentage(int64_t entry_price_cents,
                                int64_t current_price_cents) {
    if (entry_price_cents == 0) {
        return 0.0;
    }
    return static_cast<double>(current_price_cents - entry_price_cents)
         / static_cast<double>(entry_price_cents);
}

} // namespace munnir
