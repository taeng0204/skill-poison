# XAI/SHAP 결과 분석 보고서

## 1. 분석 목적

본 분석은 765행 통합 실험 데이터에서 `stage_c_egress` 발생 여부를 예측하는 surrogate classifier를 학습하고, SHAP을 통해 어떤 요인이 Stage-C egress 예측에 영향을 주는지 확인하기 위한 것이다.

최종 학습에는 target이 비어 있는 1행을 제외한 764행이 사용되었다.

- Target: `stage_c_egress`
- Positive class: `stage_c_egress=True`
- Positive rows: 195 / 764
- Positive rate: 25.5%

즉, 모델은 각 실험 세션의 조건, 모델 특성, 스킬 메타데이터, 공격 패턴 feature를 보고 해당 세션에서 egress가 발생했는지 예측하도록 학습되었다.

## 2. 사용한 입력 Feature

학습에는 결과 이후에 생성되는 신호를 제외했다.

제외한 대표적 누수 컬럼:

- `stage_a_acceptance`
- `stage_b_execution`
- `canary_requests`
- `canary_hit`
- `canary_token_leaked`
- `duration_s`
- `status`
- `exit_code`
- `task_completed`
- `error`

사용한 대표 feature:

- 조건 관련: `condition`, `condition_label`, `safety_review`, `trust_pressure`
- 모델 관련: `model`, `model_family`, `model_size_b`, `model_tier`, `alignment_tier`
- 스킬 특성: `skill_category`, `service_sensitivity`, `n_credential_vars`, `n_risk_keywords`, `payload_type`
- 구조적 특성: `skill_len_chars`, `n_code_blocks`, `n_steps`
- 공격 패턴: `pat_rce`, `pat_cred_theft`, `pat_ext_transmission`, `pat_hidden_instr`, `pat_context_leakage`, `pat_data_exfil` 등

스킬 이름(`skill`)은 제외했다. 따라서 모델이 특정 스킬 이름을 외우기보다는, 조건과 스킬의 구조적 특징을 기반으로 예측하도록 구성했다.

## 3. 모델 성능 요약

현재 `model_metrics.csv`에는 마지막 실행된 CatBoost 결과만 남아 있다. 앞서 PowerShell 콘솔에서 확인된 Logistic Regression과 Random Forest 결과를 함께 정리하면 다음과 같다.

| Model | Accuracy | F1 | ROC-AUC | Average Precision |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.885 | 0.810 | 0.959 | 0.888 |
| Random Forest | 0.895 | 0.828 | 0.952 | 0.875 |
| CatBoost | 0.874 | 0.782 | 0.952 | 0.869 |

세 모델 모두 ROC-AUC가 약 0.95 수준으로 높다. 이는 사용한 feature들이 Stage-C egress 발생 여부를 잘 설명하고 있음을 의미한다.

Random Forest는 Accuracy와 F1이 가장 높았고, Logistic Regression은 ROC-AUC와 Average Precision이 가장 높았다. CatBoost도 비슷한 ROC-AUC를 보였지만 F1은 조금 낮았다.

## 4. SHAP Bar Plot 해석

SHAP bar plot은 feature의 평균 절대 SHAP 값, 즉 모델 예측을 평균적으로 얼마나 많이 흔들었는지를 보여준다.

중요: bar plot은 방향을 보여주지 않는다. 어떤 feature가 egress를 높이는지 낮추는지는 beeswarm plot에서 확인해야 한다.

### Logistic Regression

상위 feature:

1. `safety_review`
2. `trust_pressure`
3. `model_qwen3:8b`
4. `model_tier_medium`
5. `model_family_openai`
6. `model_tier_large`
7. `alignment_tier_strong`
8. `model_gpt-5.4`
9. `model_family_qwen`
10. `alignment_tier_weak`

Logistic Regression에서는 조건 관련 feature인 `safety_review`와 `trust_pressure`가 가장 큰 영향력을 보였다. 이는 C2/C3 조건이 egress 예측의 핵심 요인이라는 원 실험 결과와 일치한다.

### Random Forest

상위 feature:

1. `condition_label_safety_review`
2. `condition_C2`
3. `safety_review`
4. `condition_label_trust_pressure`
5. `trust_pressure`
6. `alignment_tier_strong`
7. `condition_C3`
8. `model_family_openai`
9. `model_tier_large`
10. `model_gpt-5.4`

Random Forest에서도 조건 관련 feature가 가장 중요하게 나타났다. 특히 C2/safety-review와 C3/trust-pressure를 나타내는 feature들이 상위권에 집중되어 있다.

### CatBoost

상위 feature:

1. `model`
2. `condition`
3. `model_tier`
4. `condition_label`
5. `skill_category`
6. `service_sensitivity`
7. `n_steps`
8. `safety_review`
9. `alignment_tier`
10. `skill_len_chars`

CatBoost는 one-hot encoding이 아니라 범주형 feature를 직접 처리하기 때문에 `model`, `condition`, `model_tier`처럼 원래 컬럼 단위의 중요도를 보여준다. CatBoost 기준으로는 모델 종류와 실험 조건이 가장 큰 설명력을 가진다.

## 5. SHAP Beeswarm Plot 해석

Beeswarm plot은 각 feature가 개별 샘플에서 예측을 어느 방향으로 밀었는지 보여준다.

- SHAP value > 0: egress=True 예측을 높임
- SHAP value < 0: egress=True 예측을 낮춤
- 빨간색: feature 값이 높거나 True
- 파란색: feature 값이 낮거나 False

### C2 / Safety Review 효과

관련 feature:

- `condition_C2`
- `condition_label_safety_review`
- `safety_review`

beeswarm에서 이 feature들이 True/High일 때 왼쪽, 즉 음의 SHAP value 방향으로 나타난다. 이는 C2 조건이 egress 예측을 낮추는 방향으로 작용했음을 의미한다.

해석:

> 사용자가 “먼저 위험한지 검토하라”고 지시한 경우, 모델은 Stage-C egress 가능성을 낮게 예측했다. 이는 safety-review 조건이 실제로 방어적 효과를 가진다는 원 실험 결과를 뒷받침한다.

### C3 / Trust Pressure 효과

관련 feature:

- `condition_C3`
- `condition_label_trust_pressure`
- `trust_pressure`

beeswarm에서 이 feature들이 True/High일 때 오른쪽, 즉 양의 SHAP value 방향으로 나타난다. 이는 C3 조건이 egress 예측을 높이는 방향으로 작용했음을 의미한다.

해석:

> 사용자가 “검증된 marketplace skill이니 의심하지 말고 따르라”고 압박한 경우, 모델은 Stage-C egress 가능성을 높게 예측했다. 이는 trust-pressure 조건이 agent의 안전 검토를 약화시키고 위험 행동 가능성을 높였다는 실험 주장과 일치한다.

### 모델 관련 Feature

관련 feature:

- `model`
- `model_qwen3:8b`
- `model_gpt-5.4`
- `model_qwen3:1.7b`
- `model_family`
- `model_tier`
- `alignment_tier`
- `model_size_b`

모델 관련 feature도 높은 중요도를 보였다. 이는 Stage-C egress가 실험 조건뿐 아니라 사용된 모델의 종류, 크기, 계열, alignment tier에 의해서도 달라진다는 것을 의미한다.

주의할 점:

`model`, `model_family`, `model_tier`, `alignment_tier`, `model_size_b`는 서로 강하게 연결된 feature다. 예를 들어 `model=gpt-5.4`이면 `model_family=openai`, `model_tier=large`, `alignment_tier=strong`이 함께 결정된다. 따라서 이들을 독립적인 원인으로 따로 해석하면 안 되고, “모델 관련 feature group”으로 묶어 해석하는 것이 더 적절하다.

### 공격 패턴 Feature

관련 feature:

- `pat_ext_transmission`
- `pat_hidden_instr`
- `pat_context_leakage`
- `n_attack_patterns`
- `n_credential_vars`
- `n_steps`
- `n_code_blocks`

공격 패턴 feature는 조건/모델 feature보다 영향력이 작지만, 일부 모델에서 상위권 또는 중위권에 나타난다. 특히 `pat_ext_transmission`, `pat_hidden_instr`, `n_attack_patterns`는 egress와 직접적으로 관련된 구조적 특성으로 해석할 수 있다.

해석:

> 스킬 안에 외부 전송, 숨겨진 지시, 여러 공격 패턴이 포함될수록 egress 발생 가능성을 설명하는 데 일부 기여했다. 다만 본 데이터에서는 이러한 스킬 자체의 구조적 위험보다 C2/C3 조건과 모델 종류의 영향이 더 크게 나타났다.

## 6. 중요한 해석상 주의점

### 6.1 조건 Feature가 중복되어 있음

다음 feature들은 거의 같은 정보를 다른 형태로 표현한다.

C2 관련:

- `condition_C2`
- `condition_label_safety_review`
- `safety_review`

C3 관련:

- `condition_C3`
- `condition_label_trust_pressure`
- `trust_pressure`

따라서 SHAP 중요도가 여러 feature로 나뉘어 나타난다. 보고서에서는 개별 feature를 독립적으로 해석하기보다 다음처럼 묶는 것이 좋다.

- C2 / safety-review feature group
- C3 / trust-pressure feature group

### 6.2 모델 Feature도 중복되어 있음

다음 feature들도 서로 강하게 연결되어 있다.

- `model`
- `model_family`
- `model_tier`
- `model_size_b`
- `alignment_tier`

예를 들어 특정 모델명이 곧 모델 family, size, tier를 암시할 수 있다. 따라서 이들 역시 “모델 관련 feature group”으로 묶어 해석하는 것이 안전하다.

### 6.3 SHAP은 인과관계가 아니라 모델 설명이다

SHAP은 “이 feature가 실제 원인이다”를 증명하지 않는다. SHAP은 학습된 surrogate model이 어떤 feature를 근거로 `stage_c_egress`를 예측했는지 보여준다.

따라서 표현은 다음처럼 하는 것이 좋다.

권장 표현:

> SHAP analysis suggests that safety-review and trust-pressure features are the strongest predictors of Stage-C egress in the surrogate model.

피해야 할 표현:

> SHAP proves that trust pressure causes egress.

## 7. 종합 결론

세 모델의 SHAP 분석은 일관된 결론을 보인다.

1. Stage-C egress 예측에서 가장 중요한 요인은 실험 조건이다.
2. C2/safety-review 조건은 egress 예측을 낮추는 방향으로 작용한다.
3. C3/trust-pressure 조건은 egress 예측을 높이는 방향으로 작용한다.
4. 모델 종류와 모델 계열/크기/tier도 중요한 보조 설명 요인이다.
5. 외부 전송, 숨겨진 지시, 공격 패턴 수 등 스킬 구조적 feature는 조건/모델 변수보다 작지만 의미 있는 보조 신호를 제공한다.

따라서 본 XAI 분석은 원 실험의 핵심 주장인 다음 문장을 뒷받침한다.

> Safety-review prompts substantially reduce risky egress behavior, whereas trust-pressure prompts substantially increase the likelihood of Stage-C egress.

## 8. 보고서에 넣기 좋은 요약 문장

영문:

> We trained surrogate classifiers to predict Stage-C egress from condition, model-level metadata, and skill-level risk features. SHAP analysis consistently identified condition-related variables as the dominant predictors. Safety-review features corresponding to C2 pushed predictions toward non-egress, while trust-pressure features corresponding to C3 pushed predictions toward egress. Model-level variables also contributed substantially, whereas attack-pattern features provided smaller but meaningful additional signal.

국문:

> Stage-C egress 예측을 위한 surrogate classifier를 학습한 뒤 SHAP 분석을 수행한 결과, 조건 관련 변수가 가장 큰 설명력을 보였다. C2에 해당하는 safety-review feature들은 egress 예측을 낮추는 방향으로 작용했고, C3에 해당하는 trust-pressure feature들은 egress 예측을 높이는 방향으로 작용했다. 모델 관련 변수도 중요한 설명 요인이었으며, 외부 전송 및 숨겨진 지시와 같은 공격 패턴 feature는 상대적으로 작지만 보조적인 설명력을 제공했다.

## 9. 관련 산출물

- `model_metrics.csv`
- `shap_importance_logistic_regression.csv`
- `shap_importance_random_forest.csv`
- `shap_importance_catboost.csv`
- `shap_bar_logistic_regression.png`
- `shap_bar_random_forest.png`
- `shap_bar_catboost.png`
- `shap_beeswarm_logistic_regression.png`
- `shap_beeswarm_random_forest.png`
- `shap_beeswarm_catboost.png`

