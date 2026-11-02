-- Appends xecjk_korean.tex to header-includes. A pandoc -H file would
-- replace the document's own header-includes; appending keeps them.
local dir = pandoc.path.directory(PANDOC_SCRIPT_FILE)
local fh = assert(io.open(pandoc.path.join({dir, "xecjk_korean.tex"}), "r"))
local tex = fh:read("a")
fh:close()

function Meta(meta)
  local block = pandoc.MetaBlocks({pandoc.RawBlock("latex", tex)})
  local h = meta["header-includes"]
  if h == nil then
    meta["header-includes"] = pandoc.MetaList({block})
  elseif pandoc.utils.type(h) == "List" then
    h:insert(block)
    meta["header-includes"] = h
  else
    meta["header-includes"] = pandoc.MetaList({h, block})
  end
  return meta
end
