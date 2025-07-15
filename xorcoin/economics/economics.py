"""
Xorcoin Economics Module
Implements halving schedule and supply cap
"""

from typing import Tuple
import math


class XorcoinEconomics:
    """Economic parameters and calculations for Xorcoin"""
    
    # Core economic parameters
    INITIAL_BLOCK_REWARD = 50  # XOR per block
    HALVING_INTERVAL = 210_000  # blocks (same as Bitcoin)
    MAX_SUPPLY = 21_000_000  # Total XOR that will ever exist
    GENESIS_SUPPLY = 1_000_000  # Pre-mine in genesis block
    
    # Consensus parameters
    TARGET_BLOCK_TIME = 600  # 10 minutes in seconds
    BLOCKS_PER_DAY = 144  # 24 hours * 60 minutes / 10 minutes
    BLOCKS_PER_YEAR = 52_560  # 365.25 days * 144 blocks
    
    # Difficulty adjustment
    DIFFICULTY_ADJUSTMENT_INTERVAL = 2016  # blocks (~2 weeks)
    MAX_DIFFICULTY_CHANGE = 4  # Maximum 4x change per adjustment
    
    @staticmethod
    def get_block_reward(height: int) -> int:
        """
        Calculate block reward with halving schedule
        
        Args:
            height: Block height
            
        Returns:
            Block reward in XOR
        """
        if height == 0:
            # Genesis block
            return XorcoinEconomics.GENESIS_SUPPLY
            
        # Calculate number of halvings
        halvings = (height - 1) // XorcoinEconomics.HALVING_INTERVAL
        
        # Initial reward after genesis
        reward = XorcoinEconomics.INITIAL_BLOCK_REWARD
        
        # Apply halvings
        for _ in range(halvings):
            reward //= 2
            
        return reward
    
    @staticmethod
    def get_total_supply_at_height(height: int) -> int:
        """
        Calculate total supply mined up to a given height
        
        Args:
            height: Block height
            
        Returns:
            Total XOR in circulation
        """
        if height < 0:
            return 0
            
        total = XorcoinEconomics.GENESIS_SUPPLY
        
        # Calculate supply from mining
        current_reward = XorcoinEconomics.INITIAL_BLOCK_REWARD
        blocks_remaining = height
        
        while blocks_remaining > 0 and current_reward > 0:
            # How many blocks at this reward level?
            blocks_at_this_reward = min(
                blocks_remaining,
                XorcoinEconomics.HALVING_INTERVAL - ((height - blocks_remaining) % XorcoinEconomics.HALVING_INTERVAL)
            )
            
            total += blocks_at_this_reward * current_reward
            blocks_remaining -= blocks_at_this_reward
            
            # Check for halving
            if (height - blocks_remaining) % XorcoinEconomics.HALVING_INTERVAL == 0:
                current_reward //= 2
                
        return total
    
    @staticmethod
    def get_halving_schedule() -> list:
        """Get the halving schedule with dates and rewards"""
        schedule = []
        current_reward = XorcoinEconomics.INITIAL_BLOCK_REWARD
        halving_number = 0
        
        while current_reward >= 1:
            height = halving_number * XorcoinEconomics.HALVING_INTERVAL
            
            # Calculate approximate date
            blocks_since_genesis = height
            days_since_genesis = blocks_since_genesis / XorcoinEconomics.BLOCKS_PER_DAY
            years_since_genesis = days_since_genesis / 365.25
            
            # Calculate supply at this halving
            total_supply = XorcoinEconomics.get_total_supply_at_height(height)
            
            schedule.append({
                'halving': halving_number,
                'height': height,
                'reward': current_reward,
                'years_from_start': round(years_since_genesis, 2),
                'total_supply': total_supply,
                'percentage_mined': round((total_supply / XorcoinEconomics.MAX_SUPPLY) * 100, 2)
            })
            
            halving_number += 1
            current_reward //= 2
            
        return schedule
    
    @staticmethod
    def estimate_mining_end() -> dict:
        """Estimate when mining rewards will end"""
        # Find when rewards become 0
        last_halving = 0
        reward = XorcoinEconomics.INITIAL_BLOCK_REWARD
        
        while reward >= 1:
            last_halving += 1
            reward //= 2
            
        last_reward_block = last_halving * XorcoinEconomics.HALVING_INTERVAL
        
        # Calculate time
        total_days = last_reward_block / XorcoinEconomics.BLOCKS_PER_DAY
        total_years = total_days / 365.25
        
        # Calculate final supply
        final_supply = XorcoinEconomics.get_total_supply_at_height(last_reward_block)
        
        return {
            'last_reward_block': last_reward_block,
            'years_until_end': round(total_years, 2),
            'final_supply': final_supply,
            'unmined_forever': XorcoinEconomics.MAX_SUPPLY - final_supply
        }
    
    @staticmethod
    def calculate_inflation_rate(height: int) -> float:
        """Calculate annual inflation rate at given height"""
        current_reward = XorcoinEconomics.get_block_reward(height)
        current_supply = XorcoinEconomics.get_total_supply_at_height(height)
        
        if current_supply == 0 or current_reward == 0:
            return 0.0
            
        # Annual new coins
        annual_new_coins = current_reward * XorcoinEconomics.BLOCKS_PER_YEAR
        
        # Inflation rate
        inflation_rate = (annual_new_coins / current_supply) * 100
        
        return round(inflation_rate, 4)


class DifficultyAdjustment:
    """Enhanced difficulty adjustment algorithm"""
    
    @staticmethod
    def calculate_next_difficulty(
        blocks: list,
        current_difficulty: int
    ) -> int:
        """
        Calculate next difficulty based on recent blocks
        Uses a more sophisticated algorithm than the current implementation
        """
        if len(blocks) < DifficultyAdjustment.DIFFICULTY_ADJUSTMENT_INTERVAL:
            return current_difficulty
            
        # Get the adjustment period blocks
        period_blocks = blocks[-XorcoinEconomics.DIFFICULTY_ADJUSTMENT_INTERVAL:]
        
        # Calculate actual time taken
        actual_time = period_blocks[-1].timestamp - period_blocks[0].timestamp
        
        # Expected time for this many blocks
        expected_time = (XorcoinEconomics.DIFFICULTY_ADJUSTMENT_INTERVAL - 1) * XorcoinEconomics.TARGET_BLOCK_TIME
        
        # Calculate adjustment ratio
        ratio = actual_time / expected_time
        
        # Limit adjustment to prevent attacks
        if ratio < 0.25:
            ratio = 0.25
        elif ratio > 4.0:
            ratio = 4.0
            
        # Calculate new difficulty
        # If blocks were too fast (ratio < 1), increase difficulty
        # If blocks were too slow (ratio > 1), decrease difficulty
        if ratio < 1:
            # Increase difficulty
            new_difficulty = current_difficulty + max(1, int((1 - ratio) * 2))
        else:
            # Decrease difficulty
            new_difficulty = max(1, current_difficulty - int((ratio - 1) * 2))
            
        return new_difficulty


# Example usage and analysis
if __name__ == "__main__":
    print("=== Xorcoin Economic Model ===\n")
    
    # Show halving schedule
    print("Halving Schedule:")
    print("-" * 80)
    print(f"{'Halving':<10} {'Block Height':<15} {'Reward (XOR)':<15} {'Years':<10} {'Supply %':<10}")
    print("-" * 80)
    
    for halving in XorcoinEconomics.get_halving_schedule():
        print(f"{halving['halving']:<10} {halving['height']:<15,} {halving['reward']:<15} "
              f"{halving['years_from_start']:<10} {halving['percentage_mined']:<10}%")
    
    # Mining end estimate
    print("\n" + "="*80)
    end_info = XorcoinEconomics.estimate_mining_end()
    print(f"\nMining will effectively end at:")
    print(f"  Block: {end_info['last_reward_block']:,}")
    print(f"  Years: ~{end_info['years_until_end']} years from genesis")
    print(f"  Final Supply: {end_info['final_supply']:,} XOR")
    print(f"  Forever Unmined: {end_info['unmined_forever']:,} XOR")
    
    # Current economics (example at different heights)
    print("\n" + "="*80)
    print("\nEconomics at Different Heights:")
    print("-" * 80)
    
    test_heights = [0, 1000, 210_000, 420_000, 630_000, 1_000_000]
    
    for height in test_heights:
        reward = XorcoinEconomics.get_block_reward(height)
        supply = XorcoinEconomics.get_total_supply_at_height(height)
        inflation = XorcoinEconomics.calculate_inflation_rate(height)
        
        print(f"\nHeight {height:,}:")
        print(f"  Block Reward: {reward} XOR")
        print(f"  Total Supply: {supply:,} XOR")
        print(f"  Annual Inflation: {inflation}%")
    
    # Time estimates
    print("\n" + "="*80)
    print("\nTime Estimates:")
    print(f"  Blocks per day: {XorcoinEconomics.BLOCKS_PER_DAY}")
    print(f"  Blocks per year: {XorcoinEconomics.BLOCKS_PER_YEAR:,}")
    print(f"  First halving in: ~{210_000/XorcoinEconomics.BLOCKS_PER_YEAR:.1f} years")
    print(f"  Difficulty adjustment: Every {XorcoinEconomics.DIFFICULTY_ADJUSTMENT_INTERVAL:,} blocks "
          f"(~{XorcoinEconomics.DIFFICULTY_ADJUSTMENT_INTERVAL/XorcoinEconomics.BLOCKS_PER_DAY:.1f} days)")
