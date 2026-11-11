import type { AnalyzeResponse, AgentName, Claim, Source } from './state'

export type AnalysisStreamEvent =
  | { agent: AgentName; status: 'started' | 'done'; data: Record<string, unknown> }
  | { agent: 'complete'; data: AnalyzeResponse }

const sources: Source[] = [
  { id: 'src_01', title: 'Global Electricity Review 2025', domain: 'ember-energy.org', url: 'https://ember-energy.org/latest-insights/global-electricity-review-2025/', snippet: 'Renewables generated more than one third of global electricity in 2024, with solar and wind accounting for most growth.', score: 0.96 },
  { id: 'src_02', title: 'Renewable Capacity Statistics 2025', domain: 'irena.org', url: 'https://www.irena.org/Publications/2025/Mar/Renewable-capacity-statistics-2025', snippet: 'Global renewable power capacity continued to expand rapidly through 2024.', score: 0.92 },
  { id: 'src_03', title: 'Global Electricity Mid-Year Insights 2025', domain: 'iea.org', url: 'https://www.iea.org/reports/global-energy-review-2025/electricity', snippet: 'Wind and solar together supplied around 15% of global electricity in 2024.', score: 0.91 },
  { id: 'src_04', title: 'Renewables 2024: Analysis and forecast', domain: 'iea.org', url: 'https://www.iea.org/reports/renewables-2024', snippet: 'Solar PV and wind are the largest sources of new renewable electricity generation.', score: 0.88 },
  { id: 'src_05', title: 'Renewable Capacity Statistics 2025: China', domain: 'irena.org', url: 'https://www.irena.org/Publications/2025/Mar/Renewable-capacity-statistics-2025', snippet: 'China accounted for the largest share of renewable capacity additions in 2024.', score: 0.94 },
  { id: 'src_06', title: 'Global Energy Review 2025: Solar', domain: 'iea.org', url: 'https://www.iea.org/reports/global-energy-review-2025/renewables', snippet: 'China led global solar PV deployment, adding more capacity than any other market.', score: 0.9 },
  { id: 'src_07', title: 'Global Market Outlook for Solar Power 2025–2029', domain: 'solarpowereurope.org', url: 'https://www.solarpowereurope.org/insights/outlooks/global-market-outlook-for-solar-power-2025-2029', snippet: 'Cumulative installed solar capacity passed the two-terawatt threshold during 2024.', score: 0.89 },
  { id: 'src_08', title: 'Renewable Capacity Statistics 2025: Solar', domain: 'irena.org', url: 'https://www.irena.org/Publications/2025/Mar/Renewable-capacity-statistics-2025', snippet: 'Global solar capacity reached a new high after record installations in 2024.', score: 0.86 },
  { id: 'src_09', title: 'Global Electricity Review 2025: Power additions', domain: 'ember-energy.org', url: 'https://ember-energy.org/latest-insights/global-electricity-review-2025/', snippet: 'Renewables made up the vast majority of net new power capacity added worldwide in 2024.', score: 0.93 },
  { id: 'src_10', title: 'Renewable Capacity Statistics 2025: Additions', domain: 'irena.org', url: 'https://www.irena.org/Publications/2025/Mar/Renewable-capacity-statistics-2025', snippet: 'Renewable sources represented over 90% of total power capacity additions in 2024.', score: 0.91 },
  { id: 'src_11', title: 'Renewables 2024: Capacity growth', domain: 'iea.org', url: 'https://www.iea.org/reports/renewables-2024', snippet: 'Renewables are expected to account for almost all global power capacity growth.', score: 0.83 },
  { id: 'src_12', title: 'Electricity 2025: Renewables snapshot', domain: 'energyinst.org', url: 'https://www.energyinst.org/statistical-review', snippet: 'Renewable generation and installed capacity both increased across major markets.', score: 0.78 },
]

const extractedClaims: Claim[] = [
  { id: 'claim_01', text: 'Renewable sources generated more than one third of global electricity in 2024.', category: 'statistical', verdict: null, confidence: null, reasoning: null, supporting_sources: [], contradicting_sources: [] },
  { id: 'claim_02', text: 'Solar and wind supplied most of the increase in renewable electricity generation in 2024.', category: 'factual', verdict: null, confidence: null, reasoning: null, supporting_sources: [], contradicting_sources: [] },
  { id: 'claim_03', text: 'China added more solar capacity than any other country in 2024.', category: 'statistical', verdict: null, confidence: null, reasoning: null, supporting_sources: [], contradicting_sources: [] },
  { id: 'claim_04', text: 'Global installed solar capacity passed two terawatts during 2024.', category: 'statistical', verdict: null, confidence: null, reasoning: null, supporting_sources: [], contradicting_sources: [] },
  { id: 'claim_05', text: 'Renewables made up more than 90% of global power capacity additions in 2024.', category: 'statistical', verdict: null, confidence: null, reasoning: null, supporting_sources: [], contradicting_sources: [] },
]

const verifiedClaims: Claim[] = [
  { ...extractedClaims[0], verdict: 'SUPPORTED', confidence: 0.91, reasoning: 'Independent electricity datasets place the renewable share above one third for 2024.', supporting_sources: ['src_01', 'src_02'] },
  { ...extractedClaims[1], verdict: 'SUPPORTED', confidence: 0.88, reasoning: 'Generation data consistently identifies wind and solar as the main growth sources.', supporting_sources: ['src_03', 'src_04'] },
  { ...extractedClaims[2], verdict: 'SUPPORTED', confidence: 0.95, reasoning: 'Capacity datasets show China led all markets in new solar installations.', supporting_sources: ['src_05', 'src_06'] },
  { ...extractedClaims[3], verdict: 'INCONCLUSIVE', confidence: 0.61, reasoning: 'Estimates vary by source and by whether distributed systems are included.', supporting_sources: ['src_07'], contradicting_sources: ['src_08'] },
  { ...extractedClaims[4], verdict: 'SUPPORTED', confidence: 0.89, reasoning: 'Two independent capacity datasets place renewables above the 90% threshold.', supporting_sources: ['src_09', 'src_10', 'src_11'] },
]

const contradiction = {
  claim_id: 'claim_04',
  source_a_id: 'src_07',
  source_b_id: 'src_08',
  conflict_description: 'Reported cumulative solar capacity differs around the two-terawatt threshold because datasets treat distributed installations differently.',
}

const report = `# Renewable electricity in 2024\n\nRenewables supplied more than one third of global electricity in 2024, with solar and wind driving most of the increase. China led new solar deployment, while source methods differ on whether cumulative solar capacity crossed two terawatts during the year.\n\n## Findings\n\nThree of the five claims are supported with high confidence. The global electricity share, leading sources of growth, China’s solar additions, and renewables’ share of new power capacity are corroborated across independent datasets.\n\n## Remaining uncertainty\n\nEstimates of cumulative solar capacity vary with the treatment of distributed systems. The threshold claim remains inconclusive until reporting methods align.\n\n## Conclusion\n\nThe evidence points to continued rapid renewable expansion in 2024, with a clear caveat around capacity accounting.`

function makeCompleteResponse(query: string): AnalyzeResponse {
  const now = new Date().toISOString()
  return {
    job_id: 'mock_job_veritas_001',
    status: 'completed',
    query,
    created_at: now,
    completed_at: now,
    summary: {
      total_claims: 5,
      supported_claims: 4,
      refuted_claims: 0,
      inconclusive_claims: 1,
      total_sources: 12,
      contradictions_detected: 1,
    },
    claims: verifiedClaims,
    sources,
    contradictions: [contradiction],
    report_markdown: report,
    errors: [],
  }
}

export function playMockStream(query: string, onEvent: (event: AnalysisStreamEvent) => void): () => void {
  const events: AnalysisStreamEvent[] = [
    { agent: 'claim_extractor', status: 'started', data: {} },
    { agent: 'claim_extractor', status: 'done', data: { claims: extractedClaims } },
    { agent: 'search_retriever', status: 'started', data: {} },
    { agent: 'search_retriever', status: 'done', data: { sources } },
    { agent: 'fact_verifier', status: 'started', data: {} },
    { agent: 'fact_verifier', status: 'done', data: { claims: verifiedClaims } },
    { agent: 'contradiction_detector', status: 'started', data: {} },
    { agent: 'contradiction_detector', status: 'done', data: { contradictions: [contradiction] } },
    { agent: 'report_generator', status: 'started', data: {} },
    { agent: 'report_generator', status: 'done', data: { report_markdown: report } },
    { agent: 'complete', data: makeCompleteResponse(query) },
  ]
  const timers = events.map((event, index) =>
    window.setTimeout(() => onEvent(event), 320 * (index + 1)),
  )

  return () => timers.forEach(window.clearTimeout)
}
