" I need mouse because i am a pleb "
:set mouse=a

" Set tab to 4 spaces "
:set tabstop=2
:set shiftwidth=2
:set expandtab

:set number

:set confirm

:let mapleader = ","

" Remapping for saving files "
:nnoremap <C-s> <Cmd>:w<CR>

" Shortcut to use HopWord basic usage "
:nnoremap <leader>h <Cmd>HopWord<CR>

" Jump to implementation "
:nnoremap <leader>[ <Cmd>:pop<CR>

" Toggle Filetree "
:nnoremap <leader>y <Cmd>NvimTreeToggle<CR>
:nnoremap <leader>t <Cmd>NvimTreeFocus<CR>

" Telescope shortcuts for file search and grep "
:nnoremap <leader>f :Telescope find_files<CR>
:nnoremap <leader>g :Telescope live_grep<CR>

" Move to previous/next file"
nnoremap <silent>    <A-,> <Cmd>BufferPrevious<CR>
nnoremap <silent>    <A-.> <Cmd>BufferNext<CR>
" " Goto buffer in position...
nnoremap <silent>    <A-1> <Cmd>BufferGoto 1<CR>
nnoremap <silent>    <A-2> <Cmd>BufferGoto 2<CR>
nnoremap <silent>    <A-3> <Cmd>BufferGoto 3<CR>
nnoremap <silent>    <A-4> <Cmd>BufferGoto 4<CR>
nnoremap <silent>    <A-5> <Cmd>BufferGoto 5<CR>
nnoremap <silent>    <A-6> <Cmd>BufferGoto 6<CR>
nnoremap <silent>    <A-7> <Cmd>BufferGoto 7<CR>
nnoremap <silent>    <A-8> <Cmd>BufferGoto 8<CR>
nnoremap <silent>    <A-9> <Cmd>BufferGoto 9<CR>
nnoremap <silent>    <A-0> <Cmd>BufferLast<CR>
" " Pin/unpin buffer
nnoremap <silent>    <A-p> <Cmd>BufferPin<CR>
" " Close buffer
nnoremap <silent>    <A-c> <Cmd>BufferClose<CR>
