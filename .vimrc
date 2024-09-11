map <C-n> :set nu<CR>
map <C-p> :set nonu<CR>
map gda} {d}
map gC :wa<CR>:!dotnet run :6006 localhost:6007<CR>
map gP :wa<CR>:!pudb3 "%" --test<CR>
map gc :wa<CR>:!g++ -std=c++14 "%" && ./a.out --test
map gh :wa<CR>:!python3 "%" --help<CR>
map gj :wa<CR>:!"$(readlink -f "%")" --test<CR>
map gl :ls<CR>
map gn :wa<CR>:!node "%" --test<CR>
map gp :wa<CR>:!python "%" --test<CR>
map gq :wa<CR>:!psql -f "%"<CR>
map gw :wa<CR>
set autoindent
set background=dark
set hlsearch
set scrolloff=0
set shiftwidth=4
set tabstop=4
syntax on
filetype indent plugin on
autocmd FileType c setlocal shiftwidth=4 tabstop=4
autocmd FileType cpp setlocal shiftwidth=4 tabstop=4
autocmd FileType cs setlocal expandtab softtabstop=2 shiftwidth=2 tabstop=8
autocmd FileType html setlocal expandtab softtabstop=2 shiftwidth=2 tabstop=8
autocmd FileType javascript setlocal expandtab softtabstop=2 shiftwidth=2 tabstop=8
autocmd FileType json setlocal expandtab softtabstop=2 shiftwidth=2 tabstop=8
autocmd FileType python setlocal expandtab softtabstop=4 shiftwidth=4 tabstop=8
autocmd FileType typescript setlocal expandtab softtabstop=2 shiftwidth=2 tabstop=8
autocmd FileType typescriptreact setlocal expandtab softtabstop=2 shiftwidth=2 tabstop=8
colorscheme evening
