class Validator:
    def __init__(
        self,
        logger,
        *,
        margin_limit=1.0,
        high_liquidity_threshold=1_000_000,
        margin_override_tickers=None,
    ):
        self.logger = logger
        self.margin_limit = margin_limit
        self.high_liquidity_threshold = high_liquidity_threshold
        if margin_override_tickers is None:
            margin_override_tickers = {"ITSA3", "ITSA4", "ITSA8"}
        self.margin_override_tickers = {
            ticker.upper() for ticker in (margin_override_tickers or [])
        }
        
    def check_market_cap_consistency(self, ticker, val1, val2):
        """
        Verifica consistência entre duas fontes de Market Cap.
        Se max/min > 3 -> Inconsistente.
        """
        if val1 is None or val2 is None or val1 == 0 or val2 == 0:
            return True # Cannot compare, assume ok or handle elsewhere
            
        v_min = min(val1, val2)
        v_max = max(val1, val2)
        
        if v_max / v_min > 3:
            self.logger.log_exclusion(
                ticker, 
                "INCONSISTENCY_MARKET_CAP", 
                f"Source divergence > 3x ({val1} vs {val2})"
            )
            return False
        return True

    def validate_metrics(self, row):
        """
        Valida métricas individuais de uma empresa.
        Retorna True se válido, False se deve ser marcado/excluído.
        """
        # Margem Líquida Anual fora de [-100%, +100%]
        # Assumindo margem em percentual (ex: 12.0) ou decimal (0.12)?
        # Fundamentus costuma vir decimal. Ajustar conforme dado real.
        # Regra: "margem anual fora de [-100%, +100%]" -> [-1.0, 1.0] se decimal

        net_margin = row.get('net_margin')
        if net_margin is not None:
            if (
                net_margin < -self.margin_limit
                or net_margin > self.margin_limit
            ):
                ticker = row.get('ticker', '').upper()
                liq_2m = row.get('liq_2m') or 0.0

                if self._should_ignore_margin(row, ticker, liq_2m):
                    # Ignora margem para holdings/empresas de alta liquidez com outliers conhecidos.
                    self.logger.info(
                        f"Ignoring net margin outlier for {ticker}: "
                        f"net_margin={net_margin}, liq_2m={liq_2m}"
                    )
                    row['net_margin'] = None
                else:
                    self.logger.log_exclusion(
                        ticker,
                        "OUTLIER_MARGIN",
                        f"Annual margin {net_margin:.2%} out of range [-100%, 100%]"
                    )
                    return False # Ou marcar como suspeito? O prompt diz "Marcar como suspeito... Se não houver correção -> excluir"
                                 # Para Fase 0, vamos excluir para garantir integridade.
        
        # P/L > 200 -> Suspeito/Outlier
        pl = row.get('p_l')
        if pl is not None and pl > 200:
             self.logger.log_exclusion(
                row['ticker'],
                "OUTLIER_PL",
                f"P/L {pl} > 200"
            )
             return False

        return True

    def check_pl_validity(self, profit):
        """
        P/L = market_cap / lucro_liquido
        Lucro <= 0 -> P/L Inválido.
        """
        if profit is None or profit <= 0:
            return False
        return True

    def _should_ignore_margin(self, row, ticker, liq_2m):
        """
        Decide se devemos ignorar margens fora do limite.
        Holdings e casos de alta liquidez podem ter margens contábeis extremas.
        """
        sector = str(row.get('sector') or '').lower()
        subsector = str(row.get('subsector') or '').lower()

        holding_keywords = ("holding", "particip")
        is_holding = any(
            keyword in sector or keyword in subsector
            for keyword in holding_keywords
        )

        if is_holding:
            return True

        if ticker in self.margin_override_tickers:
            return True

        if liq_2m >= self.high_liquidity_threshold and net_margin_positive(row):
            return True

        return False


def net_margin_positive(row):
    net_margin = row.get('net_margin')
    try:
        return net_margin is not None and net_margin > 0
    except TypeError:
        return False
