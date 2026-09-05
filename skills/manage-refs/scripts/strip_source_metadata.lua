-- Applied after citeproc. Citation formatting is complete; local input paths
-- must not be exported into Word custom properties or other output metadata.
function Meta(meta)
  meta.csl = nil
  meta.bibliography = nil
  return meta
end
