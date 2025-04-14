import pygame
import sys
from stockfish import Stockfish  # NEW: Import Stockfish library

from const import *
from game import Game
from square import Square
from move import Move
from piece import *

class Main:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess')
        self.game = Game()
        # NEW: Initialize game mode and Stockfish
        self.game_mode = self.select_game_mode()
        self.stockfish = None
        if self.game_mode == "2":
            # Initialize Stockfish for AI mode
            # Adjust the path to your Stockfish executable
            self.stockfish = Stockfish(path="D:\\OneDrive\\VoHuuKhang\\1University\\242\\NMAI\\BTL\\BTL3\\stockfish\\stockfish-windows-x86-64-avx2.exe")
            self.stockfish.set_skill_level(10)  # Adjustable: 0 (easy) to 20 (hard)
            self.move_list = []  # Track moves for Stockfish

    def select_game_mode(self):
        # NEW: Prompt user to select game mode
        while True:
            mode = input("Chọn chế độ chơi (1: Người vs Người, 2: Người vs Máy): ")
            if mode in ["1", "2"]:
                return mode
            print("Vui lòng chọn 1 hoặc 2.")

    def make_ai_move(self, board, game):
        # NEW: Compute and apply AI move
        # Update Stockfish with current position instead of move history
        current_fen = self.convert_board_to_fen(board)  # Hàm này cần được thêm vào
        self.stockfish.set_fen_position(current_fen)
        
        # Get best move (limit to 1 second for responsiveness)
        best_move = self.stockfish.get_best_move_time(3000)
        if best_move:
            # Parse UCI move (e.g., "e2e4")
            from_square = best_move[:2]
            to_square = best_move[2:4]
            files = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
            
            from_row = 8 - int(from_square[1])  # Convert chess notation to array indices
            from_col = files[from_square[0]]
            to_row = 8 - int(to_square[1])
            to_col = files[to_square[0]]
            
            # Get the piece at the starting position
            piece = board.squares[from_row][from_col].piece
            if piece and piece.color == 'black':  # Ensure we're moving a black piece
                # Create Move object
                initial = Square(from_row, from_col)
                final = Square(to_row, to_col)
                move = Move(initial, final)
                
                # Calculate valid moves for this piece
                board.calc_moves(piece, from_row, from_col, bool=True)
                
                # Check if the move is valid
                if board.valid_move(piece, move):
                    captured = board.squares[to_row][to_col].has_piece()
                    board.move(piece, move)
                    board.set_true_en_passant(piece)
                    
                    # Add move to history for display purposes
                    self.move_list.append(best_move)
                    
                    game.play_sound(captured)
                    # Update display
                    game.show_bg(self.screen)
                    game.show_last_move(self.screen)
                    game.show_pieces(self.screen)
                    game.next_turn()
                else:
                    print(f"Invalid AI move: {best_move} - not in calculated moves")
            else:
                print(f"Invalid AI move: {best_move} - no piece at position")
        else:
            print("Stockfish returned no move.")

    def convert_board_to_fen(self, board):
        """Convert the current board state to FEN notation for Stockfish"""
        fen = ""
        for row in range(ROWS):
            empty = 0
            for col in range(COLS):
                square = board.squares[row][col]
                if square.has_piece():
                    if empty > 0:
                        fen += str(empty)
                        empty = 0
                    piece = square.piece
                    symbol = self.get_piece_symbol(piece)
                    fen += symbol
                else:
                    empty += 1
            if empty > 0:
                fen += str(empty)
            if row < 7:
                fen += "/"
        
        # Add active color
        fen += " w " if self.game.next_player == 'white' else " b "
        
        # Add castling availability (simplified)
        castling = ""
        # White kingside
        if self.has_castling_rights(board, 'white', 'kingside'):
            castling += "K"
        # White queenside
        if self.has_castling_rights(board, 'white', 'queenside'):
            castling += "Q"
        # Black kingside
        if self.has_castling_rights(board, 'black', 'kingside'):
            castling += "k"
        # Black queenside
        if self.has_castling_rights(board, 'black', 'queenside'):
            castling += "q"
        
        fen += castling if castling else "-"
        
        # Add en passant target square (simplified)
        fen += " - "
        
        # Add halfmove clock and fullmove number (simplified)
        fen += "0 1"
        
        return fen

    def get_piece_symbol(self, piece):
        """Return the FEN symbol for a piece"""
        symbol = {
            'pawn': 'p',
            'knight': 'n',
            'bishop': 'b',
            'rook': 'r',
            'queen': 'q',
            'king': 'k'
        }
        # White pieces are uppercase, black pieces are lowercase
        return symbol[piece.name].upper() if piece.color == 'white' else symbol[piece.name]

    def has_castling_rights(self, board, color, side):
        """Check if a side has castling rights"""
        # Get the row based on color
        row = 7 if color == 'white' else 0
        
        # Check if king is in original position and hasn't moved
        king_col = 4
        king_square = board.squares[row][king_col]
        if not king_square.has_piece() or not isinstance(king_square.piece, King) or king_square.piece.moved:
            return False
        
        # Check if rook is in original position and hasn't moved
        rook_col = 7 if side == 'kingside' else 0
        rook_square = board.squares[row][rook_col]
        return (rook_square.has_piece() and 
                isinstance(rook_square.piece, Rook) and 
                not rook_square.piece.moved)

    def mainloop(self):
        screen = self.screen
        game = self.game
        board = self.game.board
        dragger = self.game.dragger

        while True:
            # Show methods
            game.show_bg(screen)
            game.show_last_move(screen)
            game.show_moves(screen)
            game.show_pieces(screen)
            game.show_hover(screen)

            if dragger.dragging:
                dragger.update_blit(screen)

            # NEW: Handle AI move if in AI mode and it's AI's turn
            if self.game_mode == "2" and game.next_player == 'black' and not dragger.dragging:
                self.make_ai_move(board, game)
                pygame.display.update()
                continue  # Skip event processing until AI move is done

            for event in pygame.event.get():

                # Click
                if event.type == pygame.MOUSEBUTTONDOWN:
                    dragger.update_mouse(event.pos)

                    clicked_row = dragger.mouseY // SQSIZE
                    clicked_col = dragger.mouseX // SQSIZE

                    # If clicked square has a piece
                    if board.squares[clicked_row][clicked_col].has_piece():
                        piece = board.squares[clicked_row][clicked_col].piece
                        # Valid piece (color)?
                        if piece.color == game.next_player:
                            board.calc_moves(piece, clicked_row, clicked_col, bool=True)
                            dragger.save_initial(event.pos)
                            dragger.drag_piece(piece)
                            # Show methods
                            game.show_bg(screen)
                            game.show_last_move(screen)
                            game.show_moves(screen)
                            game.show_pieces(screen)

                # Mouse motion
                elif event.type == pygame.MOUSEMOTION:
                    motion_row = event.pos[1] // SQSIZE
                    motion_col = event.pos[0] // SQSIZE

                    game.set_hover(motion_row, motion_col)

                    if dragger.dragging:
                        dragger.update_mouse(event.pos)
                        # Show methods
                        game.show_bg(screen)
                        game.show_last_move(screen)
                        game.show_moves(screen)
                        game.show_pieces(screen)
                        game.show_hover(screen)
                        dragger.update_blit(screen)

                # Click release
                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragger.dragging:
                        dragger.update_mouse(event.pos)

                        released_row = dragger.mouseY // SQSIZE
                        released_col = dragger.mouseX // SQSIZE

                        # Create possible move
                        initial = Square(dragger.initial_row, dragger.initial_col)
                        final = Square(released_row, released_col)
                        move = Move(initial, final)

                        # Valid move?
                        if board.valid_move(dragger.piece, move):
                            # Normal capture
                            captured = board.squares[released_row][released_col].has_piece()
                            board.move(dragger.piece, move)
                            board.set_true_en_passant(dragger.piece)
                            # NEW: Record move in UCI format for Stockfish
                            if self.game_mode == "2":
                                uci_move = (
                                    chr(97 + dragger.initial_col) + str(8 - dragger.initial_row) +
                                    chr(97 + released_col) + str(8 - released_row)
                                )
                                self.move_list.append(uci_move)
                            # Sounds
                            game.play_sound(captured)
                            # Show methods
                            game.show_bg(screen)
                            game.show_last_move(screen)
                            game.show_pieces(screen)
                            # Next turn
                            game.next_turn()

                    dragger.undrag_piece()

                # Key press
                elif event.type == pygame.KEYDOWN:
                    # Changing themes
                    if event.key == pygame.K_t:
                        game.change_theme()
                    # Reset game
                    if event.key == pygame.K_r:
                        game.reset()
                        game = self.game
                        board = self.game.board
                        dragger = self.game.dragger
                        # NEW: Reset move list for AI mode
                        if self.game_mode == "2":
                            self.move_list = []

                # Quit application
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            pygame.display.update()

main = Main()
main.mainloop()